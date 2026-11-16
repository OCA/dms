/* Copyright 2026 Tecnativa - Carlos Roca
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl). */
import {registry} from "@web/core/registry";

const row = (text) => `.o_dms_tree_row:has(.o_dms_tree_label:contains('${text}'))`;
function dragEvent(type) {
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(
        new File(["tour upload"], "tour_upload.txt", {type: "text/plain"})
    );
    return new DragEvent(type, {bubbles: true, cancelable: true, dataTransfer});
}

const node = (text) => `.o_dms_tree_node:has(> ${row(text)})`;

/**
 * Drag a node of the tree and drop it over another one, like a user would do.
 *
 * @param {HTMLElement} source row of the dragged node
 * @param {HTMLElement} target row of the node to drop on
 */
function dragAndDropNode(source, target) {
    const dataTransfer = new DataTransfer();
    const fire = (el, type) =>
        el.dispatchEvent(
            new DragEvent(type, {bubbles: true, cancelable: true, dataTransfer})
        );
    fire(source, "dragstart");
    fire(target, "dragenter");
    fire(target, "dragover");
    fire(target, "drop");
    fire(source, "dragend");
}

registry.category("web_tour.tours").add("dms_field_tree_tour", {
    steps: () => [
        {
            content: "Open the DMS tab of the partner",
            trigger: ".o_notebook .nav-link:contains('DMS')",
            run: "click",
        },
        {
            content: "The whole tree is loaded and open",
            trigger: `${node("Tour Folder")}[aria-expanded='true'] ${row("tour.txt")}`,
        },
        // Selection and preview
        {
            content: "Select the folder",
            trigger: row("Tour Folder"),
            run: "click",
        },
        {
            content: "The preview shows the selected folder",
            trigger: ".o_preview_directory h3:contains('Tour Folder')",
        },
        // Inline rename from the context menu
        {
            content: "Open the context menu of the folder",
            trigger: row("Tour Folder"),
            run: ({anchor}) =>
                anchor.dispatchEvent(
                    new MouseEvent("contextmenu", {bubbles: true, cancelable: true})
                ),
        },
        {
            content: "Paste is disabled as nothing has been cut",
            trigger: ".o_dms_context_menu [data-action='paste']:disabled",
        },
        {
            content: "Rename the folder",
            trigger: ".o_dms_context_menu [data-action='rename']",
            run: "click",
        },
        {
            content: "Type the new name",
            trigger: ".o_dms_tree_rename",
            run: "edit Tour Renamed",
        },
        {
            content: "Confirm the new name",
            trigger: ".o_dms_tree_rename",
            run: "press Enter",
        },
        {
            content: "The folder is renamed",
            trigger: `${row("Tour Renamed")}:not(:has(input))`,
        },
        // Cut and paste with the toolbar
        {
            content: "Select the file",
            trigger: row("tour.txt"),
            run: "click",
        },
        {
            content: "The preview shows tour.txt",
            trigger: ".o_preview_directory h3:contains('tour.txt')",
        },
        {
            content: "Cut the file",
            trigger: ".o_dms_action_cut:enabled",
            run: "click",
        },
        {
            content: "The file is shown as cut",
            trigger: `.o_dms_tree_row_cut:contains('tour.txt')`,
        },
        {
            content: "Select the destination folder",
            trigger: row("Tour Target"),
            run: "click",
        },
        {
            content: "The preview shows Tour Target",
            trigger: ".o_preview_directory h3:contains('Tour Target')",
        },
        {
            content: "Paste the file",
            trigger: ".o_dms_action_paste:enabled",
            run: "click",
        },
        {
            content: "The file has been moved",
            trigger: `${node("Tour Target")} ${row("tour.txt")}`,
        },
        // Move a file by dragging it over a folder
        {
            content: "Drag drag.txt to Tour Target",
            trigger: `${row("drag.txt")}[draggable='true']`,
            run: ({anchor}) => {
                // Native selectors don't support ":contains"
                const target = [...document.querySelectorAll(".o_dms_tree_row")].find(
                    (el) => el.textContent.trim() === "Tour Target"
                );
                dragAndDropNode(anchor, target);
            },
        },
        {
            content: "The dragged file has been moved",
            trigger: `${node("Tour Target")} ${row("drag.txt")}`,
        },
        {
            content: "No folder is highlighted after the drop",
            trigger: ".o_dms_tree:not(:has(.o_dms_tree_row_drop_target))",
        },
        // Rename with a double click on the name
        {
            content: "Double click the name of the file",
            trigger: `${row("drag.txt")} .o_dms_tree_label`,
            run: "dblclick",
        },
        {
            content: "The extension is shown, but can't be edited",
            trigger: ".o_dms_tree_rename_extension:contains('.txt')",
        },
        {
            content: "Type the new name, without extension",
            trigger: ".o_dms_tree_rename",
            run: "edit dragged",
        },
        {
            content: "Confirm the new name",
            trigger: ".o_dms_tree_rename",
            run: "press Enter",
        },
        {
            content: "The file is renamed keeping its extension",
            trigger: `.o_dms_tree:not(:has(.o_dms_tree_rename)) ${row("dragged.txt")}`,
        },
        // Upload by dropping a file on the selected folder
        {
            content: "Select the folder to upload to",
            trigger: row("Tour Target"),
            run: "click",
        },
        {
            content: "Drag a file over the folder details",
            trigger: ".dms_document_col_preview:has(h3:contains('Tour Target'))",
            run: ({anchor}) => anchor.dispatchEvent(dragEvent("dragenter")),
        },
        {
            content: "Drop the file on the drop zone",
            trigger: ".o-Dropzone.o_dms_dropzone",
            run: ({anchor}) => {
                anchor.dispatchEvent(dragEvent("dragover"));
                anchor.dispatchEvent(dragEvent("drop"));
            },
        },
        {
            content: "The drop zone is hidden after the drop",
            trigger: "body:not(:has(.o-Dropzone))",
        },
        {
            content: "The file is uploaded into the folder",
            trigger: `${node("Tour Target")} ${row("tour_upload.txt")}`,
        },
        // Delete with confirmation
        {
            content: "Select the renamed folder",
            trigger: row("Tour Renamed"),
            run: "click",
        },
        {
            content: "The preview shows Tour Renamed",
            trigger: ".o_preview_directory h3:contains('Tour Renamed')",
        },
        {
            content: "Delete it",
            trigger: ".o_dms_action_delete:enabled",
            run: "click",
        },
        {
            content: "Confirm the deletion",
            trigger: ".modal-footer button:contains('Delete')",
            run: "click",
        },
        {
            content: "The folder is removed from the tree",
            trigger: `.o_dms_tree:not(:has(${row("Tour Renamed")}))`,
        },
        // Keyboard navigation
        {
            content: "Focus the destination folder",
            trigger: node("Tour Target"),
            run: ({anchor}) => anchor.focus(),
        },
        {
            content: "Collapse it with the left arrow",
            trigger: node("Tour Target"),
            run: "press ArrowLeft",
        },
        {
            content: "The folder is collapsed",
            trigger: `${node("Tour Target")}[aria-expanded='false']`,
        },
    ],
});
