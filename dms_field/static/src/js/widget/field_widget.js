odoo.define("dms_field.DmsItemWidget", function (require) {
    "use strict";

    var DmsTreeRenderer = require("dms.DmsTreeRenderer");
    var relational_fields = require("web.relational_fields");

    relational_fields.FieldOne2Many.include({
        _getRenderer: function () {
            if (this.view && this.view.arch.tag === "dms_tree") {
                return DmsTreeRenderer;
            }
            return this._super.apply(this, arguments);
        },
        _render: function () {
            if (this.view && this.view.arch.tag === "dms_tree") {
                this.$el.addClass("o_field_x2many_dms_tree");
            }
            return this._super.apply(this, arguments);
        },
    });
});
