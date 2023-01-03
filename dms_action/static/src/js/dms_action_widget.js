/** ********************************************************************************
    Copyright 2022 Creu Blanca
    License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
 **********************************************************************************/

odoo.define("dms_action.button", function (require) {
    "use strict";

    var AbstractField = require("web.AbstractField");
    var registry = require("web.field_registry");

    var DMSActionField = AbstractField.extend({
        description: "Field for DMS play actions",
        template: "dms_action.FieldDMSAction",
        events: _.extend({}, AbstractField.prototype.events, {
            "click button": "_onClickDMSPlayAction",
        }),
        _onClickDMSPlayAction: function (ev) {
            ev.preventDefault();
            ev.stopPropagation();
            var button = ev.target.closest("button");
            var type = button.dataset.name;
            var self = this;
            this._rpc({
                model: this.model,
                method: "execute_action",
                args: [[this.res_id]],
                kwargs: {kwargs: {action_id: parseInt(type, 10)}},
                context: this.record.getContext({}),
            }).then(function (action) {
                if (action) {
                    self.trigger_up("do_action", {action: action});
                }
                self.trigger_up("reload");
                self.trigger_up("close_dialog");
            });
        },
    });

    registry.add("dms_action", DMSActionField);

    return DMSActionField;
});
