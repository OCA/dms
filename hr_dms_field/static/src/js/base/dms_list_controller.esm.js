import {DmsListController} from "@dms_field/views/dms_list/dms_list_controller.esm";
import {X2ManyField} from "@web/views/fields/x2many/x2many_field";
import {patch} from "@web/core/utils/patch";

function getSanitizeDMSModel() {
    return {
        // A basic user does not have access to hr.employee, only to hr.employee.public
        // (Employee Directory), we have to get the data from hr.employee because that
        // is where it is actually linked.
        sanitizeDMSModel(model) {
            if (model === "hr.employee.public") {
                return "hr.employee";
            }
            return super.sanitizeDMSModel(...arguments);
        },
    };
}

patch(DmsListController.prototype, getSanitizeDMSModel());
patch(X2ManyField.prototype, getSanitizeDMSModel());
