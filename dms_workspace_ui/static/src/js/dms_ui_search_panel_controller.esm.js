/** @odoo-module **/

import {browser} from "@web/core/browser/browser";
import {directoryFromSearchPanelValue} from "@dms_workspace_ui/js/dms_ui_directories.esm";
import {
    TREE_STATE_KEY,
    TREE_WIDTH_KEY,
    TREE_WIDTH_MAX,
    TREE_WIDTH_MIN,
    WORKSPACE_SELECTOR,
    clampNumber,
    focusFirstFilePaneItem,
    focusTokenForDirectory,
    isSpaceKey,
    isTextEntryTarget,
    isTypeaheadKey,
    isWorkspaceMounted,
    rememberWidth,
    storedWidth,
    updateTypeahead,
} from "@dms_workspace_ui/js/dms_ui_core.esm";
import {
    openRenameDialog,
    pasteWorkspaceClipboard,
    requestTargetDelete,
    setWorkspaceClipboard,
} from "@dms_workspace_ui/js/dms_ui_commands.esm";

const DMS_MIN_RENDERER_WIDTH = 280;

export class DmsSearchPanelController {
    constructor(component) {
        this.component = component;
    }

    get env() {
        return this.component.env;
    }

    get root() {
        return this.component.root;
    }

    get sections() {
        return this.component.sections;
    }

    get state() {
        return this.component.state;
    }

    get workspace() {
        return this.component.dmsUiWorkspace;
    }

    get typeahead() {
        return this.component.dmsUiTypeahead;
    }

    searchPanelElement() {
        return this.root?.el?.closest?.(".o_search_panel") || this.root?.el;
    }

    layoutElement() {
        return this.searchPanelElement()?.closest?.(
            ".o_component_with_search_panel, .o_controller_with_searchpanel"
        );
    }

    usesRegularSearchPanel() {
        return (
            this.env.searchModel.resModel === "dms.file" &&
            this.env.searchModel.globalContext.dms_ui_workspace
        );
    }

    visibleInspectorWidth() {
        const inspector = this.layoutElement()?.querySelector?.(".dms_ui_inspector");
        return inspector?.offsetParent ? inspector.offsetWidth : 0;
    }

    currentSearchPanelWidth() {
        return (
            storedWidth(TREE_WIDTH_KEY, false, TREE_WIDTH_MIN, TREE_WIDTH_MAX) ||
            this.searchPanelElement()?.offsetWidth ||
            TREE_WIDTH_MAX
        );
    }

    maxSearchPanelWidth() {
        const layoutWidth =
            this.layoutElement()?.clientWidth || window.innerWidth || TREE_WIDTH_MAX;
        const availableWidth =
            layoutWidth - this.visibleInspectorWidth() - DMS_MIN_RENDERER_WIDTH;
        return clampNumber(availableWidth, TREE_WIDTH_MIN, TREE_WIDTH_MAX);
    }

    preferredSearchPanelWidth() {
        return this.currentSearchPanelWidth();
    }

    searchPanelWidth() {
        return Math.min(this.preferredSearchPanelWidth(), this.maxSearchPanelWidth());
    }

    applySearchPanelWidth(width = this.searchPanelWidth()) {
        const panel = this.searchPanelElement();
        if (!panel) {
            return;
        }
        const widthPx = `${width}px`;
        panel.style.width = widthPx;
        panel.style.minWidth = widthPx;
        panel.style.maxWidth = `${this.maxSearchPanelWidth()}px`;
        this.component.width = widthPx;
    }

    reconcileSearchPanelWidth() {
        requestAnimationFrame(() => {
            if (!isWorkspaceMounted() || !this.directorySection()) {
                return;
            }
            this.applySearchPanelWidth();
        });
    }

    installSearchPanelWidthMemory() {
        this.reconcileSearchPanelWidth();
    }

    onStartResize(event) {
        if (event.button !== 0) {
            return;
        }
        const initialX = event.pageX;
        const initialWidth = this.root.el.offsetWidth;
        const resizeStoppingEvents = ["keydown", "pointerdown", "pointerup"];
        let resized = false;

        const resizePanel = (resizeEvent) => {
            resizeEvent.preventDefault();
            resizeEvent.stopPropagation();
            const maxWidth = this.maxSearchPanelWidth();
            const delta = resizeEvent.pageX - initialX;
            const newWidth = Math.min(
                maxWidth,
                Math.max(TREE_WIDTH_MIN, initialWidth + delta)
            );
            this.applySearchPanelWidth(newWidth);
            resized = true;
        };

        const stopResize = (stopEvent) => {
            if (stopEvent.type === "pointerdown" && stopEvent.button === 0) {
                return;
            }
            stopEvent.preventDefault();
            stopEvent.stopPropagation();

            document.removeEventListener("pointermove", resizePanel, true);
            resizeStoppingEvents.forEach((stoppingEvent) => {
                document.removeEventListener(stoppingEvent, stopResize, true);
            });
            document.activeElement.blur();

            if (resized) {
                const nextWidth = Number(this.component.width?.replace("px", ""));
                if (
                    Number.isFinite(nextWidth) &&
                    nextWidth >= TREE_WIDTH_MIN &&
                    nextWidth <= TREE_WIDTH_MAX
                ) {
                    rememberWidth(
                        TREE_WIDTH_KEY,
                        nextWidth,
                        TREE_WIDTH_MIN,
                        TREE_WIDTH_MAX
                    );
                }
            }
        };

        resizeStoppingEvents.forEach((stoppingEvent) => {
            document.addEventListener(stoppingEvent, stopResize, true);
        });
        document.addEventListener("pointermove", resizePanel, true);
    }

    directory(value) {
        return directoryFromSearchPanelValue(value);
    }

    focusTokenForValue(value) {
        return value?.id ? {type: "tree-directory", id: value.id} : {type: "tree-all"};
    }

    focusTokenForHeader(header) {
        const directoryId = this.headerDirectoryId(header);
        return directoryId
            ? {type: "tree-directory", id: directoryId}
            : {type: "tree-all"};
    }

    selectDirectory(section, value) {
        this.workspace.rememberFocus(this.focusTokenForValue(value));
        this.workspace.selectDirectory(this.directory(value));
        if (section.activeValueId !== value.id) {
            this.env.searchModel.toggleCategoryValue(section.id, value.id);
        }
    }

    isDirectorySection(section) {
        return (
            this.env.searchModel.resModel === "dms.file" &&
            this.env.searchModel.globalContext.dms_ui_workspace &&
            section.fieldName === "directory_id"
        );
    }

    persistExpanded(section) {
        const expanded = this.state.expanded[section.id];
        browser.localStorage.setItem(
            TREE_STATE_KEY,
            JSON.stringify(
                Object.keys(expanded)
                    .filter((key) => expanded[key])
                    .map(Number)
            )
        );
    }

    onFolderKeydown(section, value, event) {
        if (!this.isDirectorySection(section)) {
            this.onSearchPanelNavigation(section, event);
            return;
        }
        if (this.onFolderClipboardShortcut(value, event)) {
            return;
        }
        if (event.key === "Tab" && event.shiftKey) {
            event.preventDefault();
            event.stopPropagation();
            return;
        }
        if (event.key === "Tab") {
            event.preventDefault();
            event.stopPropagation();
            this.focusFirstFile();
            return;
        }
        if (event.key === "Escape") {
            event.preventDefault();
            event.stopPropagation();
            return;
        }
        if (this.onFolderTypeahead(section, value, event)) {
            return;
        }
        if (
            ["ArrowDown", "ArrowUp", "End", "Home", "PageDown", "PageUp"].includes(
                event.key
            )
        ) {
            event.preventDefault();
            event.stopPropagation();
            this.focusSearchPanelHeader(
                section,
                this.searchPanelNavigationTarget(event)
            );
            return;
        }
        if (event.key === "Delete" && value.id) {
            event.preventDefault();
            event.stopPropagation();
            this.deleteDirectory(value);
            return;
        }
        if (event.key === "F2" && value.id) {
            event.preventDefault();
            event.stopPropagation();
            openRenameDialog(this.component, this.directory(value));
            return;
        }
        if (!value.id) {
            return;
        }
        if (!["ArrowLeft", "ArrowRight"].includes(event.key) && !isSpaceKey(event)) {
            return;
        }
        event.preventDefault();
        event.stopPropagation();
        const expanded = this.state.expanded[section.id];
        if (event.key === "ArrowLeft") {
            if (value.childrenIds.length && expanded[value.id]) {
                delete expanded[value.id];
            } else if (value.parentId) {
                const parent = section.values.get(value.parentId);
                if (parent) {
                    this.focusDirectory(section, parent);
                }
            }
        } else if (event.key === "ArrowRight") {
            if (value.childrenIds.length) {
                expanded[value.id] = true;
            }
        } else if (value.childrenIds.length) {
            if (expanded[value.id]) {
                delete expanded[value.id];
            } else {
                expanded[value.id] = true;
            }
        }
        this.persistExpanded(section);
    }

    onFolderClipboardShortcut(value, event) {
        if (
            !(event.ctrlKey || event.metaKey) ||
            event.altKey ||
            isTextEntryTarget(event.target)
        ) {
            return false;
        }
        const key = event.key.toLocaleLowerCase();
        if (!["c", "v", "x"].includes(key)) {
            return false;
        }
        event.preventDefault();
        event.stopPropagation();
        if (key === "v") {
            pasteWorkspaceClipboard(
                this.component,
                this.workspace.state.selectedDirectory || this.directory(value)
            );
        } else if (value.id) {
            setWorkspaceClipboard(this.component, key === "x" ? "cut" : "copy", [
                {type: "directory", id: value.id},
            ]);
        }
        return true;
    }

    focusFirstFile() {
        this.workspace.requestContentFocus();
        if (!document.querySelector(`${WORKSPACE_SELECTOR} .dms_ui_custom_browser`)) {
            focusFirstFilePaneItem();
        }
    }

    visibleDirectoryHeaders() {
        return [...this.root.el.querySelectorAll(".dms_ui_directory_header")].filter(
            (header) => header.offsetParent
        );
    }

    focusSnapshotOptionsForHeader(header) {
        const headers = this.visibleDirectoryHeaders();
        return {
            scope: "tree",
            order: headers.map((item) => this.focusTokenForHeader(item)),
            index: Math.max(0, headers.indexOf(header)),
            fallback: {type: "tree-all"},
        };
    }

    focusDirectory(section, value) {
        this.selectDirectory(section, value);
        const token = this.focusTokenForValue(value);
        const header = this.root.el.querySelector(
            `.dms_ui_directory_header[data-directory-id="${value.id}"]`
        );
        this.workspace.rememberFocus(token, this.focusSnapshotOptionsForHeader(header));
        requestAnimationFrame(() => {
            header?.focus();
        });
    }

    adjacentDirectoryFocus(value) {
        const headers = this.visibleDirectoryHeaders();
        const currentHeader = this.root.el.querySelector(
            `.dms_ui_directory_header[data-directory-id="${value.id}"]`
        );
        const index = headers.indexOf(currentHeader);
        const nextHeader = headers[index - 1] || headers[index + 1];
        const nextId = Number(nextHeader?.dataset.directoryId || 0);
        return nextId ? {type: "tree-directory", id: nextId} : {type: "tree-all"};
    }

    expandDirectoryAncestors(section, value) {
        let parentId = value.parentId;
        while (parentId) {
            this.state.expanded[section.id][parentId] = true;
            parentId = section.values.get(parentId)?.parentId;
        }
        this.persistExpanded(section);
    }

    visibleSiblingDirectories(section, value) {
        const visibleIds = new Set(
            this.visibleDirectoryHeaders()
                .map((header) => this.headerDirectoryId(header))
                .filter(Boolean)
        );
        const parentId = value?.id ? value.parentId || false : false;
        return [...section.values.values()].filter(
            (item) =>
                item.id &&
                visibleIds.has(item.id) &&
                (item.parentId || false) === parentId
        );
    }

    directorySection() {
        return this.sections.find((section) => this.isDirectorySection(section));
    }

    headerDirectoryId(header) {
        const id = Number(header?.dataset.directoryId || 0);
        return Number.isFinite(id) && id > 0 ? id : false;
    }

    searchPanelPageSize(header) {
        const unit = header?.getBoundingClientRect().height || 28;
        return Math.max(
            1,
            Math.floor((this.root.el.clientHeight || unit * 8) / unit) - 1
        );
    }

    firstRealDirectoryHeader() {
        return this.visibleDirectoryHeaders().find((header) =>
            this.headerDirectoryId(header)
        );
    }

    searchPanelNavigationTarget(event) {
        const headers = this.visibleDirectoryHeaders();
        const currentIndex = headers.indexOf(event.currentTarget);
        if (event.key === "Home") {
            return this.firstRealDirectoryHeader() || headers[0];
        }
        if (event.key === "End") {
            const directoryHeaders = headers.filter((header) =>
                this.headerDirectoryId(header)
            );
            return (
                directoryHeaders[directoryHeaders.length - 1] ||
                headers[headers.length - 1]
            );
        }
        const deltas = {
            ArrowDown: 1,
            ArrowUp: -1,
            PageDown: this.searchPanelPageSize(event.currentTarget),
            PageUp: -this.searchPanelPageSize(event.currentTarget),
        };
        const index = Math.max(
            0,
            Math.min(headers.length - 1, currentIndex + (deltas[event.key] || 0))
        );
        return headers[index];
    }

    focusSearchPanelHeader(section, header) {
        if (!header) {
            return;
        }
        const directorySection = this.directorySection();
        const directoryId = this.headerDirectoryId(header);
        this.workspace.rememberFocus(
            this.focusTokenForHeader(header),
            this.focusSnapshotOptionsForHeader(header)
        );
        header.focus();
        if (header.classList.contains("dms_ui_directory_header") && directorySection) {
            const directory = directoryId && directorySection.values.get(directoryId);
            if (directory) {
                this.selectDirectory(directorySection, directory);
            } else {
                this.component.clearSelection(directorySection.id);
                header.click();
            }
            return;
        }
        header.click();
    }

    onSearchPanelNavigation(section, event) {
        if (event.key === "Tab" && event.shiftKey) {
            event.preventDefault();
            event.stopPropagation();
            return true;
        }
        if (!this.isDirectorySection(section)) {
            return false;
        }
        if (
            !["ArrowDown", "ArrowUp", "End", "Home", "PageDown", "PageUp"].includes(
                event.key
            )
        ) {
            return false;
        }
        event.preventDefault();
        event.stopPropagation();
        this.focusSearchPanelHeader(section, this.searchPanelNavigationTarget(event));
        return true;
    }

    onFolderTypeahead(section, value, event) {
        if (!isTypeaheadKey(event)) {
            return false;
        }
        event.preventDefault();
        event.stopPropagation();
        const query = updateTypeahead(this.typeahead, event.key);
        const values = this.visibleSiblingDirectories(section, value);
        const current = value?.id ? value : false;
        if (current?.display_name?.toLocaleLowerCase().startsWith(query)) {
            return true;
        }
        const start = Math.max(0, values.indexOf(value)) + 1;
        const ordered = [...values.slice(start), ...values.slice(0, start)];
        const match = ordered.find((item) =>
            item.display_name.toLocaleLowerCase().startsWith(query)
        );
        if (match) {
            this.expandDirectoryAncestors(section, match);
            this.focusDirectory(section, match);
        }
        return true;
    }

    deleteDirectory(value) {
        requestTargetDelete(this.component, {
            ...this.directory(value),
            focusAfter: this.adjacentDirectoryFocus(value),
        });
    }

    folderContextTarget(value) {
        return {
            ...this.directory(value),
            focusToken: focusTokenForDirectory(value),
            focusAfter: this.adjacentDirectoryFocus(value),
            items: [{type: "directory", id: value.id}],
        };
    }

    openFolderContextMenu(section, value, event) {
        if (!this.isDirectorySection(section) || !value?.id) {
            return;
        }
        const header = event.currentTarget;
        this.workspace.clearContentSelection();
        this.workspace.rememberFocus(
            focusTokenForDirectory(value),
            this.focusSnapshotOptionsForHeader(header)
        );
        header?.focus();
        this.workspace.openContextMenu(event, this.folderContextTarget(value));
    }
}
