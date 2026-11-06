/** @odoo-module **/

/** ********************************************************************************
    Copyright 2022 Creu Blanca
    Copyright 2026 Tecnativa - Adasat Torres
    License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
 **********************************************************************************/

import {DmsActionField} from "./dms_action_widget.esm";
import {registry} from "@web/core/registry";

export class DmsKanbanActionField extends DmsActionField {}

DmsKanbanActionField.template = "dms_action.FieldDMSActionButton";

registry.category("fields").add("dms_action_button", {
    component: DmsKanbanActionField,
});
