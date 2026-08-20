/** @odoo-module **/

import {useState} from "@odoo/owl";
import {browser} from "@web/core/browser/browser";
import {_t} from "@web/core/l10n/translation";
import {FormViewDialog} from "@web/views/view_dialogs/form_view_dialog";
import {dmsUiFileActions} from "@dms_workspace_ui/js/dms_ui_registries.esm";
import {
    DmsFocusTransaction,
    DmsWorkspaceWidget,
} from "@dms_workspace_ui/js/dms_ui_workspace_ui.esm";
import {
    downloadDmsFile,
    openCreateFolderDialog,
    openPreview,
    openRenameDialog,
    openWorkspaceFilePicker,
    pasteWorkspaceClipboard,
    requestTargetDelete,
    restoreTarget,
    setWorkspaceClipboard,
    targetModel,
    workspaceFileInputs,
} from "@dms_workspace_ui/js/dms_ui_commands.esm";
import {errorMessage, fileUrl} from "@dms_workspace_ui/js/dms_ui_core.esm";

function actionTransaction(component, target, options = {}) {
    return options.transaction || DmsFocusTransaction.forTarget(component, target);
}

async function executeOptionalAction(component, action, file) {
    try {
        await action.run({
            actionService: component.actionService,
            file,
            orm: component.orm,
        });
    } catch (error) {
        component.notification.add(errorMessage(error), {type: "danger"});
    }
}

function restoreOnClose(transaction) {
    return () => transaction.restoreSoon();
}

function actionRestoreOptions(transaction) {
    return {
        onClose: restoreOnClose(transaction),
    };
}

function editDetailsActionParams(target) {
    return {
        res_model: targetModel(target),
        res_id: target.id,
        views: [[false, "form"]],
        type: "ir.actions.act_window",
    };
}

function onRecordSavedRefresh(workspace) {
    return async () => {
        await workspace.refresh();
    };
}

function editDetailsDialogProps(target, params, workspace) {
    return {
        resModel: params.res_model,
        resId: params.res_id,
        title: _t("Edit Details: %(name)s", {name: target.name}),
        onRecordSaved: onRecordSavedRefresh(workspace),
    };
}

function editDetailsDialogOptions(transaction) {
    return {
        onClose: () => transaction.restoreAfterOverlayClose(),
    };
}

function pickPreferredElement(elements, predicate) {
    return elements.find(predicate) || elements[0];
}

function clickIfAvailable(elements, predicate) {
    const element = pickPreferredElement(elements, predicate);
    if (!element) {
        return false;
    }
    element.click();
    return true;
}

function clickWorkspaceFilePicker() {
    if (clickIfAvailable(workspaceFileInputs(), (input) => input.isConnected)) {
        return true;
    }
    const uploadButtons = [...document.querySelectorAll(".o_button_upload_expense")];
    if (clickIfAvailable(uploadButtons, (button) => button.offsetParent)) {
        return true;
    }
    return false;
}

export class DmsUiActions extends DmsWorkspaceWidget {
    setup() {
        super.setup();
        this.workspaceState = useState(this.workspace.state);
    }

    preview(file, options = {}) {
        return openPreview(this, file, options);
    }

    open(file) {
        browser.open(fileUrl(file), "_blank");
    }

    download(file) {
        downloadDmsFile(file);
    }

    editDetails(target, options = {}) {
        const transaction = actionTransaction(this, target, options);
        const params = editDetailsActionParams(target);
        if (this.ui.isSmall) {
            this.actionService.doAction(params, actionRestoreOptions(transaction));
            return transaction;
        }
        this.dialog.add(
            FormViewDialog,
            editDetailsDialogProps(target, params, this.workspace),
            editDetailsDialogOptions(transaction)
        );
        return transaction;
    }

    rename(target, options = {}) {
        return openRenameDialog(this, target, options);
    }

    async share(target, options = {}) {
        const transaction = actionTransaction(this, target, options);
        const action = await this.orm.call(
            targetModel(target),
            "dms_ui_get_share_action",
            [[target.id]]
        );
        await this.actionService.doAction(action, actionRestoreOptions(transaction));
        return transaction;
    }

    deleteTarget(target, options = {}) {
        return requestTargetDelete(this, target, options);
    }

    restore(target) {
        return restoreTarget(this, target);
    }

    createFolder(directory, options = {}) {
        return openCreateFolderDialog(
            this,
            directory,
            directory?.focusToken || directory || false,
            options
        );
    }

    addFile(options = {}) {
        return openWorkspaceFilePicker(this, clickWorkspaceFilePicker, options);
    }

    setClipboard(mode, items) {
        setWorkspaceClipboard(this, mode, items);
    }

    paste(directory) {
        return pasteWorkspaceClipboard(this, directory);
    }

    optionalActions(file) {
        return dmsUiFileActions.getAll().filter((action) => action.isVisible(file));
    }

    async runOptional(action, file) {
        await executeOptionalAction(this, action, file);
    }
}
