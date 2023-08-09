/** @odoo-module **/

// /** ********************************************************************************
//     Copyright 2020 Creu Blanca
//     Copyright 2017-2019 MuK IT GmbH
//     License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
//  **********************************************************************************/

import {registry} from "@web/core/registry";
import {patch} from "@web/core/utils/patch";
import {listView} from "@web/views/list/list_view";
import {FileListRenderer} from "./file_list_renderer.esm";
import {FileListController} from "./file_list_controller.esm";

import {FileDropZone, FileUpload} from "./dms_file_upload.esm";

patch(FileListRenderer.prototype, "file_list_renderer_dzone", FileDropZone);
patch(FileListController.prototype, "file_list_controller_upload", FileUpload);
FileListRenderer.template = "dms.ListRenderer";

export const FileListView = {
    ...listView,
    buttonTemplate: "dms.ListButtons",
    Controller: FileListController,
    Renderer: FileListRenderer,
};

registry.category("views").add("file_list", FileListView);
