/** @odoo-module */
/* Copyright 2024 Tecnativa - Carlos Roca
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl). */
import {X2ManyField} from "@web/views/fields/x2many/x2many_field";
import {patch} from "@web/core/utils/patch";
import {DmsListRenderer} from "../../dms_list/dms_list_renderer.esm";
import {DMSListControllerObject} from "../../dms_list/dms_list_controller.esm";

patch(X2ManyField.prototype, "dms_field.X2ManyField", {
    ...DMSListControllerObject,
    get rendererProps() {
        const archInfo = this.activeField.views[this.viewMode];
        const props = {
            archInfo,
            list: this.list,
            openRecord: this.openRecord.bind(this),
        };
        if (this.viewMode === "dms_list") {
            props.archInfo = archInfo;
            props.readonly = this.props.readonly;
            props.rendererActions = this.rendererActions;
            return props;
        }
        return this._super(...arguments);
    },
});
X2ManyField.components = {...X2ManyField.components, DmsListRenderer};
