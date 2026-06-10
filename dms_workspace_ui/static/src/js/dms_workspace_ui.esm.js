/** @odoo-module **/

import {useEffect, useRef, useState} from "@odoo/owl";
import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";
import {KanbanController} from "@web/views/kanban/kanban_controller";
import {ListController} from "@web/views/list/list_controller";
import "@dms_workspace_ui/js/dms_ui_workspace_service.esm";
import {DmsFocusTransaction} from "@dms_workspace_ui/js/dms_ui_workspace_ui.esm";
import {DmsUiActions} from "@dms_workspace_ui/js/dms_ui_actions.esm";
import {DmsContentBrowserController} from "@dms_workspace_ui/js/dms_ui_content_browser_controller.esm";
import {DmsUiControllerMixin} from "@dms_workspace_ui/js/dms_ui_native_controller.esm";
import {DmsInspector} from "@dms_workspace_ui/js/dms_ui_inspector.esm";
import {
    directoryFileCountLabel,
    directoryFolderCountLabel,
    dmsUiDirectorySection,
    itemKey,
    normalizeDirectoryItem,
    parentDirectoryItem,
} from "@dms_workspace_ui/js/dms_ui_directories.esm";
import {
    requestTargetDelete,
    setWorkspaceClipboard,
    targetForFileRecords,
} from "@dms_workspace_ui/js/dms_ui_commands.esm";
import {
    dmsUiColorMode,
    dmsUiColorScheme,
    errorMessage,
    fileUrl,
    normalizeFileRecord,
    recordsForList,
} from "@dms_workspace_ui/js/dms_ui_core.esm";

async function setListSelectionClipboard(controller, mode) {
    const ids = await controller.getSelectedResIds();
    setWorkspaceClipboard(
        controller,
        mode,
        ids.map((id) => ({type: "file", id}))
    );
}

function selectedTarget(controller) {
    return targetForFileRecords(controller.model.root.selection);
}

function listClipboardCallback(controller, mode) {
    return () => setListSelectionClipboard(controller, mode);
}

function fileIconFromName(name) {
    const lower = (name || "").toLocaleLowerCase();
    if (/\.(docx?|odt|rtf)$/.test(lower)) {
        return "fa-file-word-o";
    }
    if (/\.(xlsx?|ods|csv)$/.test(lower)) {
        return "fa-file-excel-o";
    }
    if (/\.(pptx?|odp)$/.test(lower)) {
        return "fa-file-powerpoint-o";
    }
    if (/\.(zip|rar|7z|tar|gz)$/.test(lower)) {
        return "fa-file-archive-o";
    }
    return "fa-file-o";
}

export class DmsUiCustomBrowserRenderer extends DmsUiActions {
    static template = "dms_workspace_ui.CustomBrowser";

    setup() {
        super.setup();
        this.rootRef = useRef("root");
        this.folderLoadToken = 0;
        this.browserState = useState({
            folders: [],
            foldersDirectoryKey: false,
            selectedKeys: [],
            loadingFolders: false,
        });
        this.contentController = new DmsContentBrowserController(this);
        useEffect(
            () => {
                this.loadFolders();
                this.syncVisibleFiles();
            },
            () => [
                this.workspaceState.selectedDirectory?.id || 0,
                this.workspaceState.selectedDirectory?.active,
                this.workspaceState.revision,
                this.searchDomainSignature,
                this.recordsSignature,
            ]
        );
        useEffect(
            () => {
                if (
                    this.workspaceState.pendingContentFocus &&
                    !this.browserState.loadingFolders &&
                    this.hasCurrentFolderItems
                ) {
                    this.workspace.consumePendingContentFocus();
                    this.contentController.focusFirstContentItem();
                }
            },
            () => [
                this.workspaceState.pendingContentFocus,
                this.browserState.loadingFolders,
                this.browserState.foldersDirectoryKey,
                this.itemsSignature,
            ]
        );
        useEffect(
            () => {
                if (
                    document.activeElement === this.rootRef.el &&
                    this.hasCurrentFolderItems &&
                    this.hasItems
                ) {
                    this.contentController.focusFirstContentItem();
                }
            },
            () => [this.browserState.foldersDirectoryKey, this.itemsSignature]
        );
        useEffect(
            () => {
                this.contentController.selection.clear();
            },
            () => [this.workspaceState.clearSelectionToken]
        );
    }

    get displayMode() {
        return "grid";
    }

    get colorScheme() {
        return dmsUiColorScheme();
    }

    get colorMode() {
        return dmsUiColorMode();
    }

    get browserClass() {
        const listRendererClass = this.displayMode === "list" ? " o_list_renderer" : "";
        return `dms_ui_custom_browser dms_ui_custom_browser_${this.displayMode}${listRendererClass}`;
    }

    get records() {
        return recordsForList(this.props.list);
    }

    get files() {
        if (!this.hasCurrentFolderItems) {
            return [];
        }
        const currentDirectoryId = this.workspaceState.selectedDirectory?.id || false;
        return this.visibleRecordsToFiles(this.records, currentDirectoryId);
    }

    visibleRecordsToFiles(records, directoryId) {
        const files = this.recordsToFiles(records);
        return directoryId
            ? files.filter((file) => file.directoryId === directoryId)
            : files;
    }

    recordsToFiles(records) {
        return records.map((record) => {
            const file = normalizeFileRecord(record);
            return {...file, key: itemKey(file)};
        });
    }

    get folders() {
        return this.hasCurrentFolderItems ? this.browserState.folders : [];
    }

    get currentFolderKey() {
        return String(this.workspaceState.selectedDirectory?.id || 0);
    }

    initializeFolderLoadState(folderKey) {
        const loadToken = ++this.folderLoadToken;
        if (this.browserState.foldersDirectoryKey !== folderKey) {
            this.browserState.folders = [];
            this.browserState.foldersDirectoryKey = false;
        }
        return {loadToken};
    }

    get hasCurrentFolderItems() {
        return this.browserState.foldersDirectoryKey === this.currentFolderKey;
    }

    get directorySection() {
        return dmsUiDirectorySection(this.env);
    }

    getCurrentDirectoryLookup(useActiveValue = false) {
        const selectedDirectory = this.workspaceState.selectedDirectory;
        const currentDirectoryId =
            selectedDirectory?.id ||
            (useActiveValue ? this.directorySection?.activeValueId : false);
        return {
            id: currentDirectoryId,
            value: currentDirectoryId
                ? this.directorySection?.values.get(currentDirectoryId)
                : false,
        };
    }

    get currentDirectoryValue() {
        return this.getCurrentDirectoryLookup(true).value;
    }

    get parentDirectoryItem() {
        const currentDirectory =
            this.getCurrentDirectoryLookup(true).value ||
            this.workspaceState.selectedDirectory;
        if (!currentDirectory?.id) {
            return false;
        }
        const parentId =
            currentDirectory.parentId ||
            this.workspaceState.selectedDirectory?.parentId;
        const parentValue = parentId
            ? this.directorySection?.values.get(parentId)
            : false;
        return parentId && !parentValue ? false : parentDirectoryItem(parentValue);
    }

    get items() {
        const parentItem = this.parentDirectoryItem;
        return [...(parentItem ? [parentItem] : []), ...this.folders, ...this.files];
    }

    get hasItems() {
        return Boolean(this.items.length);
    }

    get showLoadingState() {
        return (
            !this.hasCurrentFolderItems ||
            (this.browserState.loadingFolders && !this.hasItems)
        );
    }

    get itemsSignature() {
        return this.items.map((item) => item.key).join(",");
    }

    get recordsSignature() {
        return this.records.map((record) => `${record.id}:${record.resId}`).join(",");
    }

    get searchDomain() {
        const domain =
            this.env.searchModel.domain || this.env.searchModel.searchDomain || [];
        return Array.isArray(domain) ? domain : [];
    }

    get searchDomainSignature() {
        try {
            return JSON.stringify(this.searchDomain);
        } catch {
            return "";
        }
    }

    syncVisibleFiles() {
        this.workspace.setVisibleFiles(this.files);
    }

    async loadFolders() {
        const folderKey = this.currentFolderKey;
        const {loadToken} = this.initializeFolderLoadState(folderKey);
        const {id: selectedDirectoryId} = this.getCurrentDirectoryLookup();
        this.browserState.loadingFolders = true;
        try {
            const result = await this.orm.call(
                "dms.directory",
                "dms_ui_child_directories",
                [selectedDirectoryId, this.searchDomain]
            );
            if (loadToken === this.folderLoadToken) {
                this.browserState.folders = result.map(normalizeDirectoryItem);
                this.browserState.foldersDirectoryKey = folderKey;
                this.retainSelectedKeys();
            }
        } catch (error) {
            if (loadToken === this.folderLoadToken) {
                this.browserState.folders = [];
                this.browserState.foldersDirectoryKey = folderKey;
                this.notification.add(errorMessage(error), {type: "danger"});
            }
        } finally {
            if (loadToken === this.folderLoadToken) {
                this.browserState.loadingFolders = false;
            }
        }
    }

    retainSelectedKeys(items = this.items) {
        this.contentController.selection.retain(items);
    }

    itemIcon(item) {
        if (this.isParentDirectoryItem(item)) {
            return "fa-level-up";
        }
        if (item.type === "directory") {
            return "fa-folder";
        }
        if (item.mimetype?.startsWith("image/")) {
            return "fa-file-image-o";
        }
        if (item.mimetype === "application/pdf") {
            return "fa-file-pdf-o";
        }
        return fileIconFromName(item.name);
    }

    itemSubtitle(item) {
        if (this.isParentDirectoryItem(item)) {
            return _t("Back to %(name)s", {
                name: item.targetName || _t("All Documents"),
            });
        }
        if (item.type === "directory") {
            return this.directoryItemSubtitle(item);
        }
        return item.humanSize || item.mimetype || "";
    }

    directoryItemSubtitle(item) {
        return `${directoryFileCountLabel(item.fileCount)}, ${directoryFolderCountLabel(
            item.folderCount
        )}`;
    }

    isDirectoryItem(item) {
        return item.type === "directory" || this.isParentDirectoryItem(item);
    }

    isParentDirectoryItem(item) {
        return item.type === "parent-directory";
    }

    isImage(item) {
        return item.type === "file" && item.mimetype?.startsWith("image/");
    }

    filePreviewUrl(item) {
        return fileUrl(item);
    }

    isSelected(item) {
        return this.contentController.isSelected(item);
    }

    onFocusIn(event) {
        this.contentController.onFocusIn(event);
    }

    async selectItem(item, event = {}) {
        await this.contentController.selectItem(item, event);
    }

    async openItem(item, event = {}) {
        await this.contentController.openItem(item, event);
    }

    async openContextMenu(event, item) {
        await this.contentController.openContextMenu(event, item);
    }

    async onKeydown(event) {
        await this.contentController.onKeydown(event);
    }
}

export class DmsUiCustomListRenderer extends DmsUiCustomBrowserRenderer {
    get displayMode() {
        return "list";
    }
}

export class DmsUiCustomKanbanRenderer extends DmsUiCustomBrowserRenderer {
    get displayMode() {
        return "grid";
    }
}

export class DmsUiListController extends DmsUiControllerMixin(ListController) {
    static template = "dms_workspace_ui.ListView";
    static components = {...ListController.components, DmsInspector};

    getStaticActionMenuItems() {
        const items = {...super.getStaticActionMenuItems()};
        delete items.archive;
        delete items.delete;
        return {
            ...items,
            deleteWorkspace: {
                sequence: 35,
                icon: "fa fa-trash-o",
                description: _t("Delete"),
                callback: () => requestTargetDelete(this, selectedTarget(this)),
            },
            unarchive: {
                ...items.unarchive,
                icon: "fa fa-undo",
                description: _t("Restore"),
            },
            cut: {
                sequence: 36,
                icon: "fa fa-scissors",
                description: _t("Cut"),
                callback: listClipboardCallback(this, "cut"),
            },
            copy: {
                sequence: 37,
                icon: "fa fa-copy",
                description: _t("Copy"),
                callback: listClipboardCallback(this, "copy"),
            },
        };
    }

    get archiveDialogProps() {
        const target = selectedTarget(this);
        const transaction = DmsFocusTransaction.forTarget(this, target, {
            fallback: target || {type: "content-root"},
        });
        return {
            body: _t("Move all selected files to Deleted Files?"),
            confirmLabel: _t("Delete"),
            confirm: () => this.toggleArchiveState(true, transaction),
            cancel: () => transaction.restoreAfterOverlayClose(),
        };
    }

    async toggleArchiveState(archive, transaction = false) {
        const target = selectedTarget(this);
        const restoreTransaction =
            transaction ||
            DmsFocusTransaction.forTarget(this, target, {
                fallback: target || {type: "content-root"},
            });
        await super.toggleArchiveState(archive);
        return this.completeArchiveToggle(restoreTransaction);
    }

    async completeArchiveToggle(transaction) {
        this.workspace.clearMarkedFiles();
        this.workspace.selectFiles([]);
        await this.workspace.refresh();
        transaction.restoreSoon();
    }
}

export class DmsUiKanbanController extends DmsUiControllerMixin(KanbanController) {
    static template = "dms_workspace_ui.KanbanView";
    static components = {...KanbanController.components, DmsInspector};
}

const fileListView = registry.category("views").get("file_list");
registry.category("views").add("dms_ui_file_list", {
    ...fileListView,
    buttonTemplate: "dms_workspace_ui.ListButtons",
    Controller: DmsUiListController,
    Renderer: DmsUiCustomListRenderer,
});

const fileKanbanView = registry.category("views").get("file_kanban");
registry.category("views").add("dms_ui_file_kanban", {
    ...fileKanbanView,
    buttonTemplate: "dms_workspace_ui.KanbanButtons",
    Controller: DmsUiKanbanController,
    Renderer: DmsUiCustomKanbanRenderer,
});
