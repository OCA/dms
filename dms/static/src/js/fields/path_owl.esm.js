/** @odoo-module **/

import {registry} from "@web/core/registry";
import {Component, onWillUpdateProps} from "@odoo/owl";
import {useService} from "@web/core/utils/hooks";

class DmsPathField extends Component {
    setup() {
        super.setup();
        this.action = useService("action");
        this.formatData(this.props);
        onWillUpdateProps((nextProps) => this.formatData(nextProps));
    }

    formatData(props) {
        this.data = JSON.parse(props.value || "[]");
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

DmsPathField.supportedTypes = ["text"];
DmsPathField.template = "dms.DmsPathField";
registry.category("fields").add("path_json", DmsPathField);
