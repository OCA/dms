/** @odoo-module **/

import {browser} from "@web/core/browser/browser";
import {ConfirmationDialog} from "@web/core/confirmation_dialog/confirmation_dialog";
import {_t} from "@web/core/l10n/translation";
import {download} from "@web/core/network/download";
import {
    DmsCreateFolderDialog,
    DmsRenameDialog,
} from "@dms_workspace_ui/js/dms_ui_dialogs.esm";
import {dmsUiFileActions} from "@dms_workspace_ui/js/dms_ui_registries.esm";
import {
    directoryFromSearchPanelValue,
    dmsUiDirectorySection,
} from "@dms_workspace_ui/js/dms_ui_directories.esm";
import {DmsFocusTransaction} from "@dms_workspace_ui/js/dms_ui_workspace_ui.esm";
import {
    errorMessage,
    fileAttachment,
    fileUrl,
    focusDeleteConfirmButton,
    focusFileViewer,
    normalizeFileRecord,
    onceCallback,
    refsForFiles,
    selectedDirectoryIds,
    selectedFileIds,
} from "@dms_workspace_ui/js/dms_ui_core.esm";

function dmsUiServices(component) {
    return {
        dialog: component.dialog || component.dialogService || component.dmsUiDialog,
        notification: component.notification || component.dmsUiNotification,
        orm: component.orm || component.dmsUiOrm,
        workspace: component.workspace || component.dmsUiWorkspace,
    };
}

export const WORKSPACE_FILE_INPUT_SELECTOR = "input[type='file'][name='ufile']";

export function workspaceFileInputs() {
    return [...document.querySelectorAll(WORKSPACE_FILE_INPUT_SELECTOR)];
}

export function targetModel(target) {
    return target.type === "file" ? "dms.file" : "dms.directory";
}

export function isDescriptionEditShortcut(event) {
    return (
        (event.ctrlKey || event.metaKey) &&
        !event.altKey &&
        !event.shiftKey &&
        event.key.toLocaleLowerCase() === "e"
    );
}

export function editFocusedDescription(component) {
    const file = component.workspace.state.focusedContent;
    if (file?.type !== "file") {
        return false;
    }
    component.workspace.requestInspectorSectionEdit("description");
    return true;
}

function previewFocusTarget(file) {
    return {
        type: "file",
        id: file.id,
        localId: file.localId,
    };
}

function openFileViewerPreview(component, file) {
    component.fileViewer.open(fileAttachment(component.store, file));
    focusFileViewer();
}

export function openPreview(
    component,
    file,
    {transaction: providedTransaction = false} = {}
) {
    const transaction =
        providedTransaction ||
        DmsFocusTransaction.forTarget(component, previewFocusTarget(file));
    openFileViewerPreview(component, file);
    transaction.restoreAfterOverlayClose({waitForOpen: true});
    return transaction;
}

function armFilePickerRestore(component, transaction) {
    const services = dmsUiServices(component);
    services.workspace.setFilePickerTransaction(transaction);
    let pickerChanged = false;
    const restore = onceCallback(() => {
        const restoreTransaction = services.workspace.consumeFilePickerTransaction();
        if (restoreTransaction) {
            restoreTransaction.restoreSoon();
        }
    });
    const scheduleRestore = (delay = 250) => {
        window.setTimeout(() => {
            if (!pickerChanged) {
                restore();
            }
        }, delay);
    };
    for (const input of workspaceFileInputs()) {
        input.addEventListener(
            "change",
            (event) => {
                pickerChanged = Boolean(event.target.files?.length);
                if (!pickerChanged) {
                    scheduleRestore();
                }
            },
            {once: true}
        );
    }
    window.addEventListener("focus", () => scheduleRestore(), {once: true});
    document.addEventListener(
        "visibilitychange",
        () => {
            if (!document.hidden) {
                scheduleRestore();
            }
        },
        {once: true}
    );
    scheduleRestore(1200);
}

export function openWorkspaceFilePicker(
    component,
    opener,
    {transaction: providedTransaction = false} = {}
) {
    const transaction =
        providedTransaction ||
        new DmsFocusTransaction(component, {fallback: {type: "content-root"}});
    armFilePickerRestore(component, transaction);
    if (opener()) {
        return transaction;
    }
    component.workspace.consumeFilePickerTransaction();
    transaction.restoreSoon();
    return transaction;
}

export function targetForFileRecords(records, focusedRecord = false) {
    const files = records.map(normalizeFileRecord);
    const focusedFile = focusedRecord ? normalizeFileRecord(focusedRecord) : files[0];
    return focusedFile && {...focusedFile, items: refsForFiles(files)};
}

function targetSelectionSummary(target) {
    const directoryIds = selectedDirectoryIds(target);
    const fileIds = selectedFileIds(target);
    return {
        directoryIds,
        fileIds,
        directoryCount: directoryIds.length,
        fileCount: fileIds.length,
        itemCount: directoryIds.length + fileIds.length,
    };
}

function uploadedFileValues(attachmentData, directoryId) {
    return attachmentData.map((attachment) => ({
        name: attachment.name,
        content: attachment.datas,
        mimetype: attachment.mimetype,
        directory_id: directoryId,
    }));
}

async function createUploadedDmsFiles(controller, attachmentIds, directoryId) {
    const attachmentData = await controller.orm.call(
        "dms.file",
        "get_dms_files_from_attachments",
        [],
        {attachment_ids: attachmentIds}
    );
    await controller.orm.call(
        "dms.file",
        "create",
        [uploadedFileValues(attachmentData, directoryId)],
        {context: controller.props.context}
    );
}

function renameTargetConfirm(services, target) {
    return async (name) => services.orm.write(targetModel(target), [target.id], {name});
}

export function openRenameDialog(
    component,
    target,
    {transaction: providedTransaction = false} = {}
) {
    const services = dmsUiServices(component);
    return DmsRenameDialog.show(
        component,
        {
            name: target.name,
            confirm: renameTargetConfirm(services, target),
        },
        {
            transaction: providedTransaction,
            fallback: target,
            refresh: {tree: target.type === "directory"},
        }
    );
}

function createFolderConfirm(services, directory) {
    return (name) =>
        services.orm.call("dms.directory", "dms_ui_create_folder", [
            directory?.id || false,
            name,
        ]);
}

async function bypassDeleteConfirmation(services) {
    try {
        return await services.orm.call(
            "res.config.settings",
            "dms_ui_bypass_delete_confirmation",
            []
        );
    } catch {
        return false;
    }
}

async function runTargetMutation(component, callback) {
    const services = dmsUiServices(component);
    try {
        await callback(services);
    } catch (error) {
        services.notification.add(errorMessage(error), {type: "danger"});
    }
}

async function refreshWorkspaceState(
    workspace,
    {
        clearSelection = false,
        transaction = false,
        refreshOptions = false,
        restore = false,
    } = {}
) {
    if (clearSelection) {
        workspace.clearMarkedFiles();
        workspace.selectFiles([]);
    }
    await workspace.refresh(refreshOptions || undefined);
    if (restore) {
        transaction?.restoreSoon();
    }
}

function failUpload(
    controller,
    transaction,
    message,
    {restoreAction = false, controllerId = false} = {}
) {
    if (restoreAction && controllerId) {
        controller.actionService.restore(controllerId);
    }
    if (message) {
        controller.notification.add(message, {type: "danger"});
    }
    transaction.restoreSoon();
    return false;
}

function restoreFromInactiveFolder(services, directory, transaction, requireActive) {
    if (!directory || directory.active !== false) {
        return false;
    }
    if (!requireActive) {
        transaction.restoreSoon();
        return true;
    }
    services.notification.add(_t("Select an active destination folder first."), {
        type: "danger",
    });
    transaction.restoreSoon();
    return true;
}

async function executeTargetDelete(services, target, transaction) {
    const permanent = target.active === false;
    const {directoryIds, fileIds} = targetSelectionSummary(target);
    if (directoryIds.length) {
        if (permanent) {
            await services.orm.unlink("dms.directory", directoryIds);
        } else {
            await services.orm.call("dms.directory", "dms_ui_set_archived", [
                directoryIds,
                true,
            ]);
        }
        if ((target.focusToken || target).type !== "content-directory") {
            services.workspace.selectDirectory(false);
        }
    }
    if (fileIds.length) {
        if (permanent) {
            await services.orm.unlink("dms.file", fileIds);
        } else {
            await services.orm.call("dms.file", "action_archive", [fileIds]);
        }
    }
    await refreshWorkspaceState(services.workspace, {
        clearSelection: true,
        transaction,
        restore: true,
    });
}

function deleteDialogCopy(target, {fileCount, itemCount, permanent}) {
    const title = permanent
        ? itemCount > 1
            ? _t("Permanently Delete selected items?")
            : fileCount > 1
              ? _t("Permanently Delete selected files?")
              : _t('Permanently Delete "%(name)s"?', {name: target.name})
        : _t("Delete");
    const body = permanent
        ? _t("Permanently deleted items can not be restored.")
        : itemCount > 1
          ? _t("Move the selected items to Deleted Files?")
          : target.type === "directory"
            ? _t(
                  "Move this folder, its subfolders, and every contained file to Deleted Files?"
              )
            : fileCount > 1
              ? _t("Move the selected files to Deleted Files?")
              : _t("Move this file to Deleted Files?");
    return {
        title,
        body,
        confirmClass: permanent ? "btn-danger" : "btn-primary",
    };
}

async function executeTargetRestore(services, target) {
    const {directoryIds, fileIds} = targetSelectionSummary(target);
    if (directoryIds.length) {
        await services.orm.call("dms.directory", "dms_ui_set_archived", [
            directoryIds,
            false,
        ]);
    }
    if (fileIds.length) {
        await services.orm.call("dms.file", "action_unarchive", [fileIds]);
    }
    await refreshWorkspaceState(services.workspace, {
        clearSelection: true,
        restore: true,
    });
}

function showDeleteConfirmationDialog(services, transaction, dialogCopy, execute) {
    const restoreHooks = transaction.dialogRestoreHooks({cancel: true, dismiss: true});
    services.dialog.add(
        ConfirmationDialog,
        {
            ...restoreHooks.props,
            title: dialogCopy.title,
            body: dialogCopy.body,
            confirmClass: dialogCopy.confirmClass,
            confirmLabel: _t("Delete"),
            confirm: execute,
        },
        restoreHooks.options
    );
    focusDeleteConfirmButton();
    return transaction;
}

export async function requestTargetDelete(
    component,
    target,
    {transaction: providedTransaction = false} = {}
) {
    if (!target) {
        return;
    }
    const services = dmsUiServices(component);
    const permanent = target.active === false;
    const transaction =
        providedTransaction || DmsFocusTransaction.forTarget(component, target);
    const {fileCount, itemCount} = targetSelectionSummary(target);
    const execute = () =>
        runTargetMutation(component, async (current) =>
            executeTargetDelete(current, target, transaction)
        );
    try {
        if (await bypassDeleteConfirmation(services)) {
            await execute();
            return transaction;
        }
    } catch (error) {
        services.notification.add(errorMessage(error), {type: "danger"});
        return;
    }
    const dialogCopy = deleteDialogCopy(target, {fileCount, itemCount, permanent});
    return showDeleteConfirmationDialog(services, transaction, dialogCopy, execute);
}

export async function restoreTarget(component, target) {
    return runTargetMutation(component, (services) =>
        executeTargetRestore(services, target)
    );
}

export function setWorkspaceClipboard(component, mode, items) {
    const services = dmsUiServices(component);
    if (!items?.length) {
        return;
    }
    services.workspace.setClipboard(mode, items);
    services.notification.add(_t("Ready for Paste"), {type: "success"});
}

export function workspaceDestinationDirectory(workspace) {
    return (
        workspace.state.selectedContentDirectory || workspace.state.selectedDirectory
    );
}

export async function pasteWorkspaceClipboard(component, directory = false) {
    const services = dmsUiServices(component);
    const clipboard = services.workspace.state.clipboard;
    const destination = directory || workspaceDestinationDirectory(services.workspace);
    const transaction = DmsFocusTransaction.forTarget(component, directory, {
        fallback: false,
    });
    if (!clipboard || !destination?.id || destination.active === false) {
        transaction.restoreSoon();
        return;
    }
    return runTargetMutation(component, async () => {
        await services.orm.call("dms.directory", "dms_ui_paste", [
            destination.id,
            clipboard.mode,
            clipboard.items,
        ]);
        await refreshWorkspaceState(services.workspace, {
            transaction,
            restore: true,
            clearSelection: false,
        });
        return transaction;
    });
}

export async function navigateToParentDirectory(component) {
    const services = dmsUiServices(component);
    const workspace = services.workspace;
    const searchModel = component.env?.searchModel;
    const section = dmsUiDirectorySection(component.env);
    if (!workspace || !searchModel || !section) {
        return false;
    }
    const currentId = section?.activeValueId || workspace.state.selectedDirectory?.id;
    if (!currentId) {
        return false;
    }
    const currentValue = section.values.get(currentId);
    const parentId =
        currentValue?.parentId || workspace.state.selectedDirectory?.parentId;
    const parentValue = section.values.get(parentId);
    if (parentId && !parentValue) {
        return false;
    }
    workspace.clearMarkedFiles();
    workspace.requestContentFocus();
    if (!parentId) {
        workspace.selectDirectory(false);
        workspace.selectContentDirectory(false);
        searchModel.clearSections([section.id]);
        await workspace.refresh({tree: false});
        return true;
    }
    workspace.selectDirectory(directoryFromSearchPanelValue(parentValue));
    workspace.selectContentDirectory(false);
    if (section.activeValueId !== parentValue.id) {
        await searchModel.toggleCategoryValue(section.id, parentValue.id);
    }
    await workspace.refresh({tree: false});
    return true;
}

function availableOnlyofficeAction(file) {
    return dmsUiFileActions
        .getAll()
        .find((action) => action.id === "onlyoffice" && action.isVisible(file));
}

async function runOptionalDmsAction(component, action, file) {
    if (!action) {
        return;
    }
    await action.run({
        actionService: component.actionService,
        file,
        orm: component.orm,
    });
}

export function downloadDmsFile(file) {
    download({
        url: "/web/content",
        data: {
            id: file.id,
            download: true,
            field: "content",
            model: "dms.file",
            filename_field: "name",
            filename: file.name,
        },
    });
}

export async function runPrimaryOpenShortcut(component, file, event) {
    const onlyofficeAction = availableOnlyofficeAction(file);
    if (event.ctrlKey && event.shiftKey) {
        downloadDmsFile(file);
        return true;
    }
    if (event.shiftKey) {
        await runOptionalDmsAction(component, onlyofficeAction, file);
        return true;
    }
    if (event.ctrlKey && file.previewable) {
        browser.open(fileUrl(file), "_blank");
        return true;
    }
    if (file.previewable) {
        openPreview(component, file);
        return true;
    }
    return false;
}

export async function uploadWorkspaceFiles(controller, attachments) {
    const transaction =
        controller.workspace.consumeFilePickerTransaction() ||
        new DmsFocusTransaction(controller, {fallback: {type: "content-root"}});
    const attachmentIds = attachments.map((attachment) => attachment.id);
    const directoryId = workspaceDestinationDirectory(controller.workspace)?.id;
    const controllerId = controller.actionService.currentController.jsId;
    if (!attachmentIds.length) {
        return failUpload(
            controller,
            transaction,
            _t("An error occurred during the upload")
        );
    }
    if (!directoryId) {
        return failUpload(
            controller,
            transaction,
            _t("You must select a directory first"),
            {
                restoreAction: true,
                controllerId,
            }
        );
    }
    try {
        await createUploadedDmsFiles(controller, attachmentIds, directoryId);
        controller.actionService.restore(controllerId);
        await refreshWorkspaceState(controller.workspace, {
            transaction,
            restore: transaction.snapshot?.scope === "tree",
            clearSelection: false,
        });
    } catch (error) {
        return failUpload(controller, transaction, errorMessage(error), {
            restoreAction: true,
            controllerId,
        });
    }
}

export function openCreateFolderDialog(
    component,
    directory,
    restoreFallback,
    {requireActive = false, transaction: providedTransaction = false} = {}
) {
    const services = dmsUiServices(component);
    const transaction =
        providedTransaction ||
        new DmsFocusTransaction(component, {fallback: restoreFallback});
    if (restoreFromInactiveFolder(services, directory, transaction, requireActive)) {
        return;
    }
    return DmsCreateFolderDialog.show(
        component,
        {
            confirm: createFolderConfirm(services, directory),
        },
        {
            transaction,
            refresh: {tree: true},
        }
    );
}
