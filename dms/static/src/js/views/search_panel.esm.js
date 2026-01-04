/* Copyright 2021-2024 Tecnativa - Víctor Martínez
 * Copyright 2024 Subteno - Timothée Vannier (https://www.subteno.com).
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */

import {SearchModel} from "@web/search/search_model";

export class DMSSearchPanel extends SearchModel {
    _getCategoryDomain(excludedCategoryId) {
        const domain = super._getCategoryDomain(...arguments);
        for (const category of this.categories) {
            if (category.id === Number(excludedCategoryId)) {
                continue;
            }

            // Make sure to filter selected category only for DMS hierarchies,
            // not other Odoo models such as product categories
            // where child_of could be better than "=" operator
            if (category.activeValueId && this.resModel.startsWith("dms")) {
                domain.push([category.fieldName, "=", category.activeValueId]);
            }
            if (domain.length === 0 && this.resModel === "dms.directory") {
                domain.push([category.fieldName, "=", false]);
            }
        }
        return domain;
    }
}
