/** @odoo-module **/

import {_t} from "@web/core/l10n/translation";
import {
    navigateToParentDirectory,
    runPrimaryOpenShortcut,
} from "@dms_workspace_ui/js/dms_ui_commands.esm";
import {DmsContentKeyboardController} from "@dms_workspace_ui/js/dms_ui_content_keyboard_controller.esm";
import {DmsContentSelectionModel} from "@dms_workspace_ui/js/dms_ui_content_selection_model.esm";
import {
    clampNumber,
    focusTokenForContentItem,
    refsForItems,
    rowsForRenderedItems,
    stopEvent,
} from "@dms_workspace_ui/js/dms_ui_core.esm";

export class DmsContentBrowserController {
    constructor(renderer) {
        this.renderer = renderer;
        this.selection = new DmsContentSelectionModel(this);
        this.keyboard = new DmsContentKeyboardController(this);
    }

    get root() {
        return this.renderer.rootRef.el;
    }

    get workspace() {
        return this.renderer.workspace;
    }

    get workspaceState() {
        return this.renderer.workspaceState;
    }

    get browserState() {
        return this.renderer.browserState;
    }

    get records() {
        return this.renderer.records;
    }

    get files() {
        return this.renderer.files;
    }

    get items() {
        return this.renderer.items;
    }

    get parentDirectoryItem() {
        return this.renderer.parentDirectoryItem;
    }

    get displayMode() {
        return this.renderer.displayMode;
    }

    isParentDirectoryItem(item) {
        return this.renderer.isParentDirectoryItem(item);
    }

    isSelected(item) {
        return this.selection.isSelected(item);
    }

    selectedItems() {
        return this.selection.selectedItems();
    }

    contentItems() {
        return this.items.filter((item) => !this.isParentDirectoryItem(item));
    }

    itemElement(item) {
        return this.root?.querySelector(`[data-item-key="${item.key}"]`);
    }

    itemFromFocusTarget(target) {
        const element = target?.closest?.(".dms_ui_custom_item");
        if (!element || !this.root?.contains(element)) {
            return false;
        }
        return this.items.find((item) => item.key === element.dataset.itemKey) || false;
    }

    itemIndex(item) {
        return this.items.findIndex((candidate) => candidate.key === item?.key);
    }

    focusTokenForItem(item) {
        return focusTokenForContentItem(item);
    }

    focusOrder() {
        const order = this.items.map((item) => this.focusTokenForItem(item));
        return order.length ? order : [{type: "content-root"}];
    }

    focusItem(item) {
        requestAnimationFrame(() => this.itemElement(item)?.focus());
    }

    syncFocusedItem(item) {
        const focusToken = this.focusTokenForItem(item);
        this.workspace.rememberFocus(focusToken, {
            scope: "content",
            order: this.focusOrder(),
            index: item ? this.itemIndex(item) : 0,
            fallback: this.parentDirectoryItem
                ? {type: "parent-directory"}
                : {type: "content-root"},
        });
        if (!item || this.isParentDirectoryItem(item)) {
            this.workspace.focusContent({type: "empty"});
            return;
        }
        if (item.type === "file" || item.type === "directory") {
            this.workspace.focusContent(item);
        }
    }

    focusContentItemNow(item) {
        const element = item ? this.itemElement(item) : null;
        if (!element) {
            return false;
        }
        element.focus({preventScroll: true});
        return true;
    }

    onFocusIn(event) {
        if (event.target === this.root) {
            if (!this.renderer.hasItems) {
                this.workspace.rememberFocus(
                    {type: "content-root"},
                    {
                        scope: "content",
                        order: [{type: "content-root"}],
                        index: 0,
                    }
                );
                this.workspace.focusContent({type: "empty"});
            }
            return;
        }
        this.syncFocusedItem(this.itemFromFocusTarget(event.target));
    }

    focusAfterContentDelete(items) {
        const deletedKeys = new Set(items.map((item) => item.key));
        const visibleItems = this.contentItems();
        const firstIndex = visibleItems.findIndex((item) => deletedKeys.has(item.key));
        if (firstIndex < 0) {
            return this.workspace.captureFocus({type: "content-root"});
        }
        const survivors = visibleItems.filter((item) => !deletedKeys.has(item.key));
        const survivor = survivors[firstIndex - 1] || survivors[firstIndex];
        if (survivor) {
            return this.focusTokenForItem(survivor);
        }
        return this.parentDirectoryItem
            ? {type: "parent-directory"}
            : {type: "content-root"};
    }

    focusFirstContentItem() {
        const focusRealItem = () => {
            const item = this.contentItems()[0];
            return this.focusContentItemNow(item);
        };
        const focusOnlyParentItem = () => {
            const item = this.items.length === 1 ? this.items[0] : false;
            if (!item || !this.isParentDirectoryItem(item)) {
                return false;
            }
            const element = this.itemElement(item);
            element?.focus({preventScroll: true});
            return Boolean(element);
        };
        requestAnimationFrame(() =>
            requestAnimationFrame(() => {
                if (focusRealItem()) {
                    return;
                }
                this.root?.focus({preventScroll: true});
                window.setTimeout(() => {
                    if (focusRealItem()) {
                        return;
                    }
                    if (
                        this.renderer.hasCurrentFolderItems &&
                        !this.browserState.loadingFolders
                    ) {
                        focusOnlyParentItem();
                    }
                }, 140);
            })
        );
    }

    async syncRecordSelection(items, focusedItem = false) {
        const fileIds = this.fileIdsForItems(items);
        await this.syncSelectedRecords(fileIds);
        const selectedFiles = this.files.filter((file) => fileIds.has(file.id));
        this.workspace.setSelectedFiles(selectedFiles);
        this.syncSelectionFocus(selectedFiles, focusedItem);
    }

    fileIdsForItems(items) {
        return new Set(
            items.filter((item) => item.type === "file").map((item) => item.id)
        );
    }

    async syncSelectedRecords(fileIds) {
        for (const record of this.records) {
            const selected = fileIds.has(record.resId);
            if (record.selected !== selected) {
                await record.toggleSelection(selected);
            }
        }
    }

    syncSelectionFocus(selectedFiles, focusedItem = false) {
        if (focusedItem) {
            this.syncFocusedItem(focusedItem);
        } else if (!selectedFiles.length) {
            this.workspace.focusContent({type: "empty"});
        }
    }

    async selectItem(item, event = {}) {
        if (this.workspace.state.contextMenu) {
            this.workspace.closeContextMenu({restoreFocus: false});
            return;
        }
        if (this.isParentDirectoryItem(item)) {
            await this.focusItemOnly(item);
            return;
        }
        if (!(event.ctrlKey || event.metaKey)) {
            await this.focusItemOnly(item);
            return;
        }
        this.selection.toggle(item);
        await this.syncRecordSelection(this.selectedItems(), item);
        this.focusItem(item);
    }

    async focusItemOnly(item) {
        if (!item) {
            return;
        }
        await this.syncRecordSelection(this.selectedItems(), item);
        this.focusItem(item);
    }

    async addFocusedSelection(currentItem, targetItem) {
        this.selection.addPair(currentItem, targetItem);
        await this.syncRecordSelection(this.selectedItems(), targetItem || currentItem);
        this.focusItem(targetItem || currentItem);
    }

    async openItem(item, event = {}) {
        if (this.isParentDirectoryItem(item)) {
            await navigateToParentDirectory(this.renderer);
            return;
        }
        if (item.type === "directory") {
            await this.openDirectory(item);
            return;
        }
        await runPrimaryOpenShortcut(this.renderer, item, event);
    }

    async openDirectory(directory) {
        const categories = this.renderer.env.searchModel.categories || [];
        const section = categories.find(
            (candidate) => candidate.fieldName === "directory_id"
        );
        this.workspace.requestContentFocus();
        this.workspace.selectDirectory(directory);
        this.workspace.selectContentDirectory(false);
        this.selection.clear();
        if (section && section.activeValueId !== directory.id) {
            await this.renderer.env.searchModel.toggleCategoryValue(
                section.id,
                directory.id
            );
        }
        await this.workspace.refresh({tree: false});
    }

    contextTargetName(items, target) {
        return items.length > 1
            ? _t("%(count)s items selected", {count: items.length})
            : target.name;
    }

    contextTargetActive(items, target) {
        return items.every((item) => item.active === false) ? false : target.active;
    }

    contextTargetFocusToken(target) {
        return target.type === "file"
            ? {type: "file", id: target.id, localId: target.localId}
            : this.focusTokenForItem(target);
    }

    contextTargetColor(items, target) {
        const files = items.filter((item) => item.type === "file");
        return files.length ? files[0].color : target.color;
    }

    contextTarget(items) {
        const target = items[0];
        return {
            ...target,
            name: this.contextTargetName(items, target),
            active: this.contextTargetActive(items, target),
            focusToken: this.contextTargetFocusToken(target),
            items: refsForItems(items),
            focusAfter: this.focusAfterContentDelete(items),
            color: this.contextTargetColor(items, target),
        };
    }

    async openContextMenu(event, item) {
        if (this.isParentDirectoryItem(item)) {
            stopEvent(event);
            return;
        }
        if (!this.isSelected(item)) {
            this.selection.clear();
            await this.syncRecordSelection([], item);
            this.focusItem(item);
            this.workspace.openContextMenu(event, this.contextTarget([item]));
            return;
        }
        const selected = this.selectedItems();
        await this.syncRecordSelection(selected, item);
        this.focusItem(item);
        this.workspace.openContextMenu(event, this.contextTarget(selected));
    }

    activeItem() {
        const key =
            document.activeElement?.closest?.(".dms_ui_custom_item")?.dataset.itemKey;
        return (
            this.items.find((item) => item.key === key) ||
            this.selectedItems()[0] ||
            this.contentItems()[0] ||
            this.items[0]
        );
    }

    async focusByIndex(index) {
        const item = this.items[clampNumber(index, 0, this.items.length - 1)];
        if (item) {
            await this.focusItemOnly(item);
        }
    }

    itemRows() {
        const elements = [...this.root.querySelectorAll(".dms_ui_custom_item")];
        return rowsForRenderedItems(
            elements.map((element) => {
                const item = this.items.find(
                    (candidate) => candidate.key === element.dataset.itemKey
                );
                return item
                    ? {item, element, rect: element.getBoundingClientRect()}
                    : false;
            })
        );
    }

    pageTargetItem(item, direction) {
        const rows = this.itemRows();
        const rowIndex = rows.findIndex((row) =>
            row.items.some((renderedItem) => renderedItem.item.key === item.key)
        );
        if (rowIndex < 0) {
            return false;
        }
        const row = rows[rowIndex];
        const columnIndex = row.items.findIndex(
            (renderedItem) => renderedItem.item.key === item.key
        );
        const current = row.items[columnIndex];
        const nextRow = rows[rowIndex + 1] || rows[rowIndex - 1];
        const rowHeight = nextRow
            ? Math.abs(nextRow.top - row.top)
            : current.rect.height || 48;
        const visibleRows = Math.max(
            1,
            Math.floor((this.root?.clientHeight || rowHeight * 4) / rowHeight) - 1
        );
        const targetRow =
            rows[clampNumber(rowIndex + direction * visibleRows, 0, rows.length - 1)];
        return (
            targetRow?.items[Math.min(columnIndex, targetRow.items.length - 1)]?.item ||
            false
        );
    }

    gridColumnCount() {
        const elements = [...this.root.querySelectorAll(".dms_ui_custom_item")];
        const first = elements[0]?.getBoundingClientRect();
        if (!first) {
            return 1;
        }
        return Math.max(
            1,
            elements.filter(
                (element) =>
                    Math.abs(element.getBoundingClientRect().top - first.top) < 4
            ).length
        );
    }

    async onKeydown(event) {
        await this.keyboard.onKeydown(event);
    }
}
