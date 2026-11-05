/** @odoo-module **/

/** ********************************************************************************
    Copyright 2022 Creu Blanca
    Copyright 2026 Tecnativa - Adasat Torres
    License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
 **********************************************************************************/

import {Component} from "@odoo/owl";
import {Dropdown} from "@web/core/dropdown/dropdown";
import {DropdownItem} from "@web/core/dropdown/dropdown_item";
import {registry} from "@web/core/registry";
import {standardFieldProps} from "@web/views/fields/standard_field_props";

export class DmsActionField extends Component {
    get actions() {
        return this.props.record.data[this.props.name] || {};
    }

    async onClickDMSPlayAction(actionId) {
        const record = this.props.record;
        const {orm, action: actionService} = this.env.services;
        // Dropdown items are destroyed when their menu closes. Keep the reload
        // and service calls independent of that lifecycle so the form updates.
        const reload = () => record.model.load();
        const action = await orm.call(
            record.resModel,
            "execute_action",
            [[record.resId]],
            {
                kwargs: {action_id: Number(actionId)},
                context: record.context,
            }
        );
        if (action) {
            await actionService.doAction(action, {
                onClose: reload,
            });
        }
        await reload();
    }
}

DmsActionField.template = "dms_action.FieldDMSAction";
DmsActionField.components = {Dropdown, DropdownItem};
DmsActionField.props = {...standardFieldProps};

registry.category("fields").add("dms_action", {
    component: DmsActionField,
});
