/** @odoo-module **/
/** ********************************************************************************
    Copyright 2026 Tecnativa - Adasat Torres
    License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
**********************************************************************************/

import {DmsActionField} from "./dms_action_widget.esm";
import {FormController} from "@web/views/form/form_controller";
import {_t} from "@web/core/l10n/translation";
import {patch} from "@web/core/utils/patch";

export class DmsFormActionMenu extends DmsActionField {}

DmsFormActionMenu.template = "dms_action.ActionMenu";

patch(FormController.prototype, {
    get actionMenuItems() {
        const items = super.actionMenuItems;
        const record = this.model.root;
        if (
            record.resModel !== "dms.file" ||
            record.isNew ||
            !Object.keys(record.data.action_button || {}).length
        ) {
            return items;
        }
        return {
            ...items,
            action: [
                ...items.action,
                {
                    key: "dms_action_menu",
                    description: _t("DMS Actions"),
                    groupNumber: 200,
                    Component: DmsFormActionMenu,
                    props: {record, name: "action_button"},
                    // ActionMenus preserves component descriptors for callback items.
                    callback: () => {
                        // The section handles selection through its DropdownItems.
                    },
                },
            ],
        };
    },
});
