/* Copyright 2024 Tecnativa - Carlos Roca
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl). */
import {DmsListRenderer} from "../../dms_list/dms_list_renderer.esm";
import {X2ManyField} from "@web/views/fields/x2many/x2many_field";
import {getDMSListControllerObject} from "../../dms_list/dms_list_controller.esm";
import {patch} from "@web/core/utils/patch";

patch(X2ManyField.prototype, getDMSListControllerObject());
patch(X2ManyField.prototype, {
    get rendererProps() {
        const props = {
            archInfo: this.archInfo,
            list: this.list,
            openRecord: this.openRecord.bind(this),
        };
        if (this.props.viewMode === "dms_list") {
            props.readonly = this.props.readonly;
            props.rendererActions = this.rendererActions;
            return props;
        }
        return super.rendererProps;
    },
});
X2ManyField.components = {...X2ManyField.components, DmsListRenderer};
