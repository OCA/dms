/* Copyright 2021 Tecnativa - Víctor Martínez
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */
odoo.define("dms.SearchPanel", function (require) {
    "use strict";

    const core = require("web.core");
    const SearchPanel = require("web.SearchPanel");
    const _t = core._t;
    SearchPanel.include({
        _renderCategory: function () {
            let res = this._super.apply(this, arguments);
            if (this.model === "dms.directory") {
                // Replace label on JS because QWeb has not enough context
                const res_dom = $(res);
                res_dom.find(".o_search_panel_label_title b").html(_t("Root"));
                res = res_dom.html();
            }
            return res;
        },
        _getCategoryDomain: function () {
            var domain = this._super.apply(this, arguments);
            var field_name_need_check = false;
            if (this.model === "dms.file") {
                field_name_need_check = "directory_id";
            } else if (this.model === "dms.directory") {
                field_name_need_check = "parent_id";
            }
            if (field_name_need_check) {
                domain.forEach(function (item, key) {
                    if (item[0] === field_name_need_check && item[1] === "child_of") {
                        domain[key] = [item[0], "=", item[2]];
                    }
                });
            }
            if (
                domain.length === 0 &&
                field_name_need_check &&
                this.model === "dms.directory"
            ) {
                domain.push([field_name_need_check, "=", false]);
            }
            return domain;
        },
    });
});
