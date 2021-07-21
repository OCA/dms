/** ********************************************************************************
    Copyright 2020 Creu Blanca
    Copyright 2017-2019 MuK IT GmbH
    License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
 **********************************************************************************/

odoo.define("dms.fields_path", function(require) {
    "use strict";

    var fields = require("web.basic_fields");
    var registry = require("web.field_registry");

    var FieldPathJson = fields.FieldText.extend({
        events: _.extend({}, fields.FieldText.prototype.events, {
            "click a": "_onNodeClicked",
        }),
        init: function() {
            this._super.apply(this, arguments);
            this.max_width = this.nodeOptions.width || 500;
            this.seperator = this.nodeOptions.seperator || "/";
            this.prefix = this.nodeOptions.prefix || false;
            this.suffix = this.nodeOptions.suffix || false;
        },
        _renderReadonly: function() {
            this.$el.empty();
            this._renderPath();
        },
        _renderPath: function() {
            var text_width_measure = "";
            var path = JSON.parse(this.value || "[]");
            $.each(
                _.clone(path).reverse(),
                function(index, element) {
                    text_width_measure += element.name + "/";
                    if (text_width_measure.length >= this.max_width) {
                        this.$el.prepend($("<span/>").text(".."));
                    } else if (index === 0) {
                        if (this.suffix) {
                            this.$el.prepend($("<span/>").text(this.seperator));
                        }
                        this.$el.prepend($("<span/>").text(element.name));
                        this.$el.prepend($("<span/>").text(this.seperator));
                    } else {
                        this.$el.prepend(
                            $("<a/>", {
                                class: "oe_form_uri",
                                "data-model": element.model,
                                "data-id": element.id,
                                href: "#",
                                text: element.name,
                            })
                        );
                        if (index !== path.length - 1) {
                            this.$el.prepend($("<span/>").text(this.seperator));
                        } else if (this.prefix) {
                            this.$el.prepend($("<span/>").text(this.seperator));
                        }
                    }
                    return text_width_measure.length < this.max_width;
                }.bind(this)
            );
        },
        _onNodeClicked: function(event) {
            event.preventDefault();
            this.do_action({
                type: "ir.actions.act_window",
                res_model: $(event.currentTarget).data("model"),
                res_id: $(event.currentTarget).data("id"),
                views: [[false, "form"]],
                target: "current",
                context: {},
            });
        },
    });

    registry.add("path_json", FieldPathJson);

    return {
        FieldPathJson: FieldPathJson,
    };
});
