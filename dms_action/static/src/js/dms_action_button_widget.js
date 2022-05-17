/** ********************************************************************************
    Copyright 2022 Creu Blanca
    License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
 **********************************************************************************/

odoo.define("dms_action.button_widget", function (require) {
    "use strict";

    var AbstractField = require("web.AbstractField");
    var field_utils = require("web.field_utils");
    var registry = require("web.field_registry");
    field_utils.format.serialized = _.identity;

    var DMSActionButtonField = AbstractField.extend({
        description: "Field for DMS play actions on Kanban",
        template: "dms_action.FieldDMSActionButton",
    });

    registry.add("dms_action_button", DMSActionButtonField);

    return DMSActionButtonField;
});
