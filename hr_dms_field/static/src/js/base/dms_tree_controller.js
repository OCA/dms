odoo.define("hr_dms_field.DmsTreeController", function (require) {
    "use strict";
    var FormController = require("web.FormController");
    var DmsTreeController = require("dms.DmsTreeController");
    const DmsTreeControllerExtension = {
        sanitizeDMSModel: function (model) {
            if (model === "hr.employee.public") {
                return "hr.employee";
            }
            return this._super(...arguments);
        },
    };
    FormController.include(DmsTreeControllerExtension);
    DmsTreeController.Controller.include(DmsTreeControllerExtension);
});
