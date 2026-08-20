/** @odoo-module **/

import {useExternalListener} from "@odoo/owl";
import {useFileViewer} from "@web/core/file_viewer/file_viewer_hook";
import {useService} from "@web/core/utils/hooks";
import {
    editFocusedDescription,
    isDescriptionEditShortcut,
    navigateToParentDirectory,
    openCreateFolderDialog,
    openWorkspaceFilePicker,
    pasteWorkspaceClipboard,
    setWorkspaceClipboard,
    uploadWorkspaceFiles,
    workspaceDestinationDirectory,
} from "@dms_workspace_ui/js/dms_ui_commands.esm";
import {
    WORKSPACE_SELECTOR,
    focusFirstFilePaneItem,
    isSearchViewTarget,
    isTextEntryTarget,
    isWorkspaceEventTarget,
    isWorkspaceMounted,
    normalizeFileRecord,
    recordsForList,
    refsForFiles,
    stopEvent,
} from "@dms_workspace_ui/js/dms_ui_core.esm";

function isAltUpDirectoryShortcut(event) {
    return event.altKey && !event.ctrlKey && !event.metaKey && event.key === "ArrowUp";
}

const UPLOADED_FILE_FOCUS_RETRY_DELAYS = [120, 300, 700];

function handleFileClipboardShortcut(component, event) {
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
        pasteWorkspaceClipboard(component);
    } else {
        const workspaceState = component.workspace.state;
        const files = workspaceState.selectedFiles.length
            ? workspaceState.selectedFiles
            : workspaceState.selectedFile
              ? [workspaceState.selectedFile]
              : [];
        setWorkspaceClipboard(
            component,
            key === "x" ? "cut" : "copy",
            refsForFiles(files)
        );
    }
    return true;
}

async function handleWorkspaceKeydown(controller, event) {
    if (!isWorkspaceMounted()) {
        return;
    }
    if (event.target.closest?.(".dms_ui_context_menu")) {
        return;
    }
    if (controller.workspace.state.contextMenu) {
        if (event.key === "Escape") {
            stopEvent(event);
            controller.workspace.closeContextMenu();
            return;
        }
        stopEvent(event);
        return;
    }
    if (event.key === "ArrowDown" && isSearchViewTarget(event.target)) {
        stopEvent(event);
        controller.workspace.requestContentFocus();
        if (!document.querySelector(`${WORKSPACE_SELECTOR} .dms_ui_custom_browser`)) {
            focusFirstFilePaneItem();
        }
        return;
    }
    if (
        isDescriptionEditShortcut(event) &&
        !isTextEntryTarget(event.target) &&
        editFocusedDescription(controller)
    ) {
        stopEvent(event);
        return;
    }
    const inWorkspace = isWorkspaceEventTarget(event.target);
    if (!inWorkspace || isTextEntryTarget(event.target)) {
        return;
    }
    if (event.target.closest?.(".o_search_panel")) {
        return;
    }
    if (handleFileClipboardShortcut(controller, event)) {
        return;
    }
    if (isAltUpDirectoryShortcut(event)) {
        stopEvent(event);
        await navigateToParentDirectory(controller);
    }
}

function installWorkspaceKeyDispatcher(controller) {
    useExternalListener(
        window,
        "keydown",
        (event) => {
            handleWorkspaceKeydown(controller, event);
        },
        {capture: true}
    );
}

async function refreshWorkspace(controller, {tree = true} = {}) {
    const selectedIds = new Set(
        controller.workspace.state.selectedFiles.map((file) => file.id)
    );
    const focusedId = controller.workspace.state.selectedFile?.id;
    if (tree) {
        controller.env.searchModel.searchPanelInfo.shouldReload = true;
        await controller.env.searchModel._notify();
        await controller.env.searchModel.sectionsPromise;
        const directory = controller.workspace.state.selectedDirectory;
        const directorySection = controller.env.searchModel.categories.find(
            (section) => section.fieldName === "directory_id"
        );
        const value = directory && directorySection?.values.get(directory.id);
        controller.workspace.selectDirectory(
            value
                ? {
                      type: "directory",
                      id: value.id,
                      name: value.display_name,
                      active: !value.dms_ui_archived,
                      permissions: value.dms_ui_permissions || {},
                  }
                : false
        );
    }
    await controller.model.load();
    const records = recordsForList(controller.model.root);
    controller.workspace.setVisibleFiles(records.map(normalizeFileRecord));
    for (const record of records) {
        if (selectedIds.has(record.resId) && !record.selected) {
            await record.toggleSelection(true);
        }
    }
    const selectedRecords = records.filter((record) => record.selected);
    const focusedRecord = records.find((record) => record.resId === focusedId);
    controller.workspace.selectFiles(
        selectedRecords.map(normalizeFileRecord),
        focusedRecord ? normalizeFileRecord(focusedRecord) : false
    );
    controller.workspace.retainMarkedFiles(records.map((record) => record.resId));
    controller.workspace.bumpRevision();
}

function setupDmsUiController(controller) {
    controller.workspace = useService("dms_ui_workspace");
    controller.dialog = useService("dialog");
    controller.actionService = useService("action");
    controller.orm = useService("orm");
    controller.notification = useService("notification");
    controller.store = useService("mail.store");
    controller.fileViewer = useFileViewer();
    controller.workspace.setRefresh((options) => refreshWorkspace(controller, options));
    installWorkspaceKeyDispatcher(controller);
}

function uploadedFileElement(uploadedName) {
    return [
        ...document.querySelectorAll(
            `${WORKSPACE_SELECTOR} .dms_ui_custom_item[data-item-key^="file_"]`
        ),
    ].find(
        (item) => item.querySelector("strong")?.textContent?.trim() === uploadedName
    );
}

function focusUploadedFile(uploadedName) {
    const element = uploadedFileElement(uploadedName);
    element?.focus({preventScroll: true});
    return Boolean(element);
}

function scheduleUploadedFileFocus(uploadedName) {
    const focusUploaded = () => focusUploadedFile(uploadedName);
    requestAnimationFrame(focusUploaded);
    for (const delay of UPLOADED_FILE_FOCUS_RETRY_DELAYS) {
        window.setTimeout(focusUploaded, delay);
    }
}

export function DmsUiControllerMixin(BaseController) {
    return class extends BaseController {
        setup() {
            super.setup(...arguments);
            setupDmsUiController(this);
        }

        openDmsUiCreateFolder() {
            const directory = workspaceDestinationDirectory(this.workspace);
            openCreateFolderDialog(
                this,
                directory,
                {type: "content-root"},
                {requireActive: true}
            );
        }

        uploadDocument() {
            return openWorkspaceFilePicker(this, () => {
                super.uploadDocument(...arguments);
                return true;
            });
        }

        async onChangeFileInput() {
            const files = [...(this.fileInput?.el?.files || [])];
            const transaction = this.workspace.consumeFilePickerTransaction();
            try {
                const result = await super.onChangeFileInput(...arguments);
                if (files.length && transaction?.snapshot?.scope !== "tree") {
                    scheduleUploadedFileFocus(files[0].name);
                }
                return result;
            } catch (error) {
                transaction?.restoreSoon();
                throw error;
            } finally {
                if (
                    transaction &&
                    (!files.length || transaction.snapshot?.scope === "tree")
                ) {
                    window.setTimeout(
                        () => transaction.restoreSoon(),
                        files.length ? 0 : 120
                    );
                }
            }
        }

        onUpload(attachments) {
            return uploadWorkspaceFiles(this, attachments);
        }
    };
}
