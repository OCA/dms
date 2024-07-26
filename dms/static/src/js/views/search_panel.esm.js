/** @odoo-module **/
/* Copyright 2021-2024 Tecnativa - Víctor Martínez
 * Copyright 2024 Subteno - Timothée Vannier (https://www.subteno.com).
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */

import {SearchModel} from "@web/search/search_model";
import {registry} from "@web/core/registry";

class DMSSearchPanel extends SearchModel {
    _getCategoryDomain(excludedCategoryId) {
        const domain = super._getCategoryDomain(...arguments);
        for (const category of this.categories) {
            if (category.id === Number(excludedCategoryId)) {
                continue;
            }

            if (category.activeValueId) {
                domain.push([category.fieldName, "=", category.activeValueId]);
            }
            if (domain.length === 0 && this.resModel === "dms.directory") {
                domain.push([category.fieldName, "=", false]);
            }
        }
        return domain;
    }
}

registry.category("views").add("dms_search_panel", DMSSearchPanel);
