/** @odoo-module **/
/* Copyright 2021-2022 Tecnativa - Víctor Martínez
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */

import SearchPanelModelExtension from "@web/legacy/js/views/search_panel_model_extension";
import {patch} from "web.utils";

patch(SearchPanelModelExtension.prototype, "dms.SearchPanel", {
    _createCategoryTree(sectionId) {
        this._super.apply(this, arguments);
        if (this.config.modelName === "dms.directory") {
            const category = this.state.sections.get(sectionId);
            category.values.get(false).display_name = this.env._t("Root");
        }
    },
    _getCategoryDomain(excludedCategoryId) {
        const domain = this._super.apply(this, arguments);
        for (const category of this.categories) {
            var attrs_item = this.config.archNodes[category.index].attrs;
            if (category.id === excludedCategoryId) {
                continue;
            }

            if ("operator" in attrs_item) {
                // Modify the domain operator to show only the records in directory.
                domain.forEach(function (item, key) {
                    if (
                        item[0] === category.fieldName &&
                        item[1] !== attrs_item.operator
                    ) {
                        domain[key][1] = attrs_item.operator;
                    }
                });
                // Apply domain to show only root directories
                if (domain.length === 0 && this.config.modelName === "dms.directory") {
                    domain.push([category.fieldName, "=", false]);
                }
            }
        }
        return domain;
    },
});
