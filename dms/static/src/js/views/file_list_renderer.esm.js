/** @odoo-module */

// /** ********************************************************************************
//     Copyright 2020 Creu Blanca
//     License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
//  **********************************************************************************/

import {ListRenderer} from "@web/views/list/list_renderer";

export class FileListRenderer extends ListRenderer {
    setup() {
        super.setup();
    }
}

FileListRenderer.components = {
    ...FileListRenderer.components,
};
