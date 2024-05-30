/** @odoo-module **/

// /** ********************************************************************************
//     Copyright 2020 Creu Blanca
//     Copyright 2017-2019 MuK IT GmbH
//     Copyright 2024 Subteno - Timothée Vannier (https://www.subteno.com).
//     License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
//  **********************************************************************************/

import {
    createFileDropZoneExtension,
    createFileUploadExtension,
} from "./dms_file_upload.esm";
import {FileListRenderer} from "./file_list_renderer.esm";
import {ListController} from "@web/views/list/list_controller";
import {listView} from "@web/views/list/list_view";
import {patch} from "@web/core/utils/patch";
import {registry} from "@web/core/registry";

patch(FileListRenderer.prototype, createFileDropZoneExtension());
patch(ListController.prototype, createFileUploadExtension());
FileListRenderer.template = "dms.ListRenderer";

export const FileListView = {
    ...listView,
    buttonTemplate: "dms.ListButtons",
    Renderer: FileListRenderer,
};

registry.category("views").add("file_list", FileListView);
