/** @odoo-module **/

import {onMounted, useState} from "@odoo/owl";
import {Dialog} from "@web/core/dialog/dialog";
import {useAutofocus} from "@web/core/utils/hooks";
import {forceFocusInputRef} from "@dms_workspace_ui/js/dms_ui_core.esm";
import {DmsWorkspaceDialog} from "@dms_workspace_ui/js/dms_ui_workspace_ui.esm";

export class DmsRenameDialog extends DmsWorkspaceDialog {
    static template = "dms_workspace_ui.RenameDialog";
    static components = {Dialog};
    static props = {
        close: Function,
        confirm: Function,
        name: String,
        refresh: {type: [Object, Boolean], optional: true},
        transaction: Object,
    };

    setup() {
        super.setup();
        this.state = useState({name: this.props.name});
        this.inputRef = useAutofocus({
            refName: "nameInput",
            selectAll: true,
            mobile: true,
        });
        onMounted(() => {
            forceFocusInputRef(this.inputRef, {select: true});
        });
    }

    payload() {
        return this.state.name.trim();
    }

    validate(name) {
        return Boolean(name);
    }

    onKeydown(event) {
        if (event.key === "Enter") {
            event.preventDefault();
            this.save();
        }
    }
}

export class DmsCreateFolderDialog extends DmsWorkspaceDialog {
    static template = "dms_workspace_ui.CreateFolderDialog";
    static components = {Dialog};
    static props = {
        close: Function,
        confirm: Function,
        refresh: {type: [Object, Boolean], optional: true},
        transaction: Object,
    };

    setup() {
        super.setup();
        this.state = useState({name: ""});
        this.inputRef = useAutofocus({refName: "nameInput", mobile: true});
        onMounted(() => {
            forceFocusInputRef(this.inputRef);
        });
    }

    payload() {
        return this.state.name.trim();
    }

    validate(name) {
        return Boolean(name);
    }

    onKeydown(event) {
        if (event.key === "Enter") {
            event.preventDefault();
            this.save();
        }
    }
}
