/** @odoo-module **/

// /** ********************************************************************************
//     Copyright 2024 Subteno - Timothée Vannier (https://www.subteno.com).
//     License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
//  **********************************************************************************/
import {Component, onWillUpdateProps} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {standardFieldProps} from "@web/views/fields/standard_field_props";
import {useService} from "@web/core/utils/hooks";

class DmsPathField extends Component {
    setup() {
        super.setup();
        this.action = useService("action");
        this.formatData(this.props);
        onWillUpdateProps((nextProps) => this.formatData(nextProps));
    }

    formatData(props) {
        const path_json = props.record.data && props.record.data.path_json;
        this.data = JSON.parse(path_json || "[]");
    }

    _onNodeClicked(event) {
        event.preventDefault();
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: $(event.currentTarget).data("model"),
            res_id: $(event.currentTarget).data("id"),
            views: [[false, "form"]],
            target: "current",
            context: {},
        });
    }
}

DmsPathField.template = "dms.DmsPathField";
DmsPathField.props = {
    ...standardFieldProps,
};

const dmsPathField = {
    component: DmsPathField,
    display_name: "Dms Path Field",
    supportedTypes: ["text"],
    extractProps: () => {
        return {};
    },
};

registry.category("fields").add("path_json", dmsPathField);
