// /** ********************************************************************************
//     Copyright 2024 Subteno - Timothée Vannier (https://www.subteno.com).
//     License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
//  **********************************************************************************/
import {Component, useProps} from "@odoo/owl";
import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";
import {standardFieldProps} from "@web/views/fields/standard_field_props";
import {useService} from "@web/core/utils/hooks";

class DmsPathField extends Component {
    static template = "dms.DmsPathField";
    props = useProps(standardFieldProps);

    setup() {
        this.action = useService("action");
    }

    get data() {
        return JSON.parse(this.props.record.data.path_json || "[]");
    }

    _onNodeClicked(event) {
        event.preventDefault();
        const target = event.currentTarget;
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: target.getAttribute("data-model"),
            res_id: Number(target.getAttribute("data-id")),
            views: [[false, "form"]],
            target: "current",
            context: {},
        });
    }
}

const dmsPathField = {
    component: DmsPathField,
    displayName: _t("Dms Path Field"),
    supportedTypes: ["text"],
    extractProps: () => {
        return {};
    },
};

registry.category("fields").add("path_json", dmsPathField);
