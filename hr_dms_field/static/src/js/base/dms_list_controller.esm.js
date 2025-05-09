import {getDMSListControllerObject} from "@dms_field/views/dms_list/dms_list_controller.esm";
import {patch} from "@web/core/utils/patch";

patch(getDMSListControllerObject.prototype, {
    // A basic user does not have access to hr.employee, only to hr.employee.public
    // (Employee Directory), we have to get the data from hr.employee because that
    // is where it is actually linked.
    sanitizeDMSModel: function (model) {
        if (model === "hr.employee.public") {
            return "hr.employee";
        }
        return this._super(...arguments);
    },
});
