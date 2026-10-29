// /** ********************************************************************************
//     Copyright 2026 Tecnativa - Carlos Roca
//     License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
//  **********************************************************************************/
import {registry} from "@web/core/registry";

function dispatchDragEvent(type, files = []) {
    const dataTransfer = new DataTransfer();
    for (const file of files) {
        dataTransfer.items.add(file);
    }
    const ev = new DragEvent(type, {bubbles: true, cancelable: true, dataTransfer});
    document.querySelector(".o_content").dispatchEvent(ev);
}

registry.category("web_tour.tours").add("dms_backend_file_views_tour", {
    url: "/odoo/action-dms.action_dms_file",
    steps: () => [
        {
            content: "Kanban view is rendered with the upload button",
            trigger: ".o_kanban_renderer .o_kanban_record:contains('tour_file.txt')",
        },
        {
            content: "Upload button is shown",
            trigger: ".o_control_panel button:contains('Upload')",
        },
        {
            content: "Select the tour directory in the search panel",
            trigger: ".o_search_panel_category_value header:contains('Tour Directory')",
            run: "click",
        },
        {
            content: "Drag a file over the view",
            trigger: ".o_kanban_renderer",
            run: () => dispatchDragEvent("dragover"),
        },
        {
            content: "Drop zone is shown",
            trigger: ".o_dropzone",
            run: () =>
                dispatchDragEvent("drop", [
                    new File(["tour upload"], "tour_upload.txt", {type: "text/plain"}),
                ]),
        },
        {
            content: "Dropped file is uploaded",
            trigger: ".o_kanban_record:contains('tour_upload.txt')",
        },
        {
            content: "Switch to list view",
            trigger: ".o_switch_view.o_list",
            run: "click",
        },
        {
            content: "List view is rendered with the upload button",
            trigger: ".o_list_renderer .o_data_row:contains('tour_file.txt')",
        },
        {
            content: "Upload button is shown in list view",
            trigger: ".o_control_panel button:contains('Upload')",
        },
        {
            content: "Open the file",
            trigger: ".o_data_row .o_data_cell:contains('tour_file.txt')",
            run: "click",
        },
        {
            content: "Path field shows the directory",
            trigger: ".o_form_view .o_field_path_json :contains('Tour Directory')",
        },
    ],
});

registry.category("web_tour.tours").add("dms_backend_directory_children_tour", {
    url: "/odoo/action-dms.action_dms_directory",
    steps: () => [
        {
            content: "Child directories are not listed at root level",
            trigger:
                ".o_kanban_renderer:has(.o_kanban_record:contains('Tour Directory')):not(:has(.o_kanban_record:contains('Tour Child Directory')))",
        },
        {
            content: "Open the subdirectories of the tour directory",
            trigger:
                ".o_kanban_record:contains('Tour Directory') a[name='action_dms_directories_all_directory']",
            run: "click",
        },
        {
            content: "The child directory is shown",
            trigger: ".o_kanban_record:contains('Tour Child Directory')",
        },
    ],
});
