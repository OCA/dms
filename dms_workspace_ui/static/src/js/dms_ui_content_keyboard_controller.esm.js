/** @odoo-module **/

import {
    editFocusedDescription,
    isDescriptionEditShortcut,
    openRenameDialog,
    requestTargetDelete,
} from "@dms_workspace_ui/js/dms_ui_commands.esm";
import {
    clampNumber,
    focusDirectoryTree,
    focusSearchViewInput,
    isEnterKey,
    isSpaceKey,
    isTypeaheadKey,
    stopEvent,
    updateTypeahead,
} from "@dms_workspace_ui/js/dms_ui_core.esm";

export class DmsContentKeyboardController {
    constructor(browser) {
        this.browser = browser;
    }

    get workspace() {
        return this.browser.workspace;
    }

    get browserState() {
        return this.browser.browserState;
    }

    get items() {
        return this.browser.items;
    }

    async onKeydown(event) {
        if (this.workspace.state.contextMenu) {
            if (event.key === "Escape") {
                stopEvent(event);
                this.workspace.closeContextMenu();
            }
            return;
        }
        if (event.key === "Tab") {
            stopEvent(event);
            focusDirectoryTree();
            return;
        }
        if (event.key === "Escape") {
            await this.clearSelection(event);
            return;
        }
        const item = this.browser.activeItem();
        if (!item) {
            return;
        }
        if (await this.handleTypeahead(event, item)) {
            return;
        }
        if (await this.handleMovement(event, item)) {
            return;
        }
        await this.handleAction(event, item);
    }

    async clearSelection(event) {
        stopEvent(event);
        const item = this.browser.activeItem();
        this.browser.selection.clear();
        this.workspace.clearMarkedFiles();
        await this.browser.syncRecordSelection([], item);
        if (item) {
            this.browser.focusItem(item);
        }
    }

    async handleTypeahead(event, item) {
        if (!isTypeaheadKey(event)) {
            return false;
        }
        stopEvent(event);
        const query = updateTypeahead(this.workspace.state.fileTypeahead, event.key);
        if ((item.name || "").toLocaleLowerCase().startsWith(query)) {
            return true;
        }
        const start = this.browser.itemIndex(item) + 1;
        const ordered = [...this.items.slice(start), ...this.items.slice(0, start)];
        const match = ordered.find((candidate) =>
            (candidate.name || "").toLocaleLowerCase().startsWith(query)
        );
        if (match) {
            await this.browser.focusItemOnly(match);
        }
        return true;
    }

    async handleMovement(event, item) {
        const index = this.browser.itemIndex(item);
        const columns =
            this.browser.displayMode === "grid" ? this.browser.gridColumnCount() : 1;
        const moves = {
            ArrowDown: columns,
            ArrowLeft: -1,
            ArrowRight: 1,
            ArrowUp: -columns,
        };
        if (event.key === "PageDown" || event.key === "PageUp") {
            stopEvent(event);
            await this.focusTargetItem(
                item,
                this.browser.pageTargetItem(item, event.key === "PageDown" ? 1 : -1),
                event
            );
            return true;
        }
        if (event.key in moves) {
            stopEvent(event);
            if (event.key === "ArrowUp" && index < columns && !event.shiftKey) {
                focusSearchViewInput();
                return true;
            }
            const target =
                this.items[
                    clampNumber(index + moves[event.key], 0, this.items.length - 1)
                ];
            await this.focusTargetItem(item, target, event);
            return true;
        }
        if (event.key === "Home" || event.key === "End") {
            stopEvent(event);
            await this.browser.focusByIndex(
                event.key === "Home" ? 0 : this.items.length - 1
            );
            return true;
        }
        return false;
    }

    async focusTargetItem(item, target, event) {
        if (!target) {
            return;
        }
        if (event.shiftKey) {
            await this.browser.addFocusedSelection(item, target);
        } else {
            await this.browser.focusItemOnly(target);
        }
    }

    async handleAction(event, item) {
        if (isSpaceKey(event)) {
            stopEvent(event);
            await this.browser.selectItem(item, {ctrlKey: true});
            return;
        }
        if (isEnterKey(event)) {
            stopEvent(event);
            await this.browser.openItem(item, event);
            return;
        }
        if (isDescriptionEditShortcut(event)) {
            stopEvent(event);
            if (item.type === "file") {
                await this.browser.focusItemOnly(item);
                editFocusedDescription(this.browser.renderer);
            }
            return;
        }
        if (event.key === "F2") {
            stopEvent(event);
            if (!this.browser.isParentDirectoryItem(item)) {
                openRenameDialog(
                    this.browser.renderer,
                    this.browser.contextTarget([item])
                );
            }
            return;
        }
        if (event.key === "Delete") {
            stopEvent(event);
            if (!this.browser.isParentDirectoryItem(item)) {
                const selectedItems = this.browser.selectedItems();
                const items = selectedItems.length ? selectedItems : [item];
                requestTargetDelete(
                    this.browser.renderer,
                    this.browser.contextTarget(items)
                );
            }
        }
    }
}
