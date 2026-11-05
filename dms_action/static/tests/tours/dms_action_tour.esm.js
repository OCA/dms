/** @odoo-module **/

import {registry} from "@web/core/registry";

registry.category("web_tour.tours").add("dms_action_kanban_menu", {
    test: true,
    steps: () => [
        {
            content: "Open the file card menu",
            trigger: ".o_kanban_record .o_dropdown_kanban .dropdown-toggle",
        },
        {
            content: "Check the separate DMS section and group visibility",
            trigger: ".o_kanban_card_manage_title:contains(DMS Actions)",
            run() {
                const titles = [
                    ...document.querySelectorAll(".o_kanban_card_manage_title"),
                ];
                if (!titles.some((title) => title.textContent.trim() === "Actions")) {
                    throw new Error("The standard Actions section must remain visible");
                }
                const items = [...document.querySelectorAll(".dropdown-item")];
                if (
                    items.some((item) =>
                        item.textContent.includes("Forbidden DMS action")
                    )
                ) {
                    throw new Error("An action restricted to another group is visible");
                }
            },
        },
        {
            content: "Execute the DMS action from the card menu",
            trigger: ".o_kanban_record .dropdown-item:contains(Tour DMS action)",
        },
        {
            content: "Check that the card reflects the lock without opening the form",
            trigger: ".o_kanban_record .o_dms_file_kanban_lock .fa-unlock-alt",
            run() {
                if (document.querySelector(".o_form_view")) {
                    throw new Error("Executing the action must keep the kanban open");
                }
            },
        },
    ],
});

registry.category("web_tour.tours").add("dms_action_form_menu", {
    test: true,
    steps: () => [
        {
            content: "Open the standard form action menu",
            trigger: ".o_form_view .o_cp_action_menus .dropdown-toggle",
        },
        {
            content: "Check the DMS section and its allowed actions",
            trigger: ".dropdown-header:contains(DMS Actions)",
            run() {
                if (document.querySelector(".o_form_view .o_dms_action")) {
                    throw new Error("The standalone DMS dropdown must not be rendered");
                }
                const items = [...document.querySelectorAll(".dropdown-item")];
                if (
                    items.some((item) =>
                        item.textContent.includes("Forbidden DMS action")
                    )
                ) {
                    throw new Error("An action restricted to another group is visible");
                }
            },
        },
        {
            content: "Execute the DMS action from the standard menu",
            trigger: ".dropdown-item:contains(Tour DMS action)",
        },
        {
            content: "Check that the action ran and the form was reloaded",
            trigger: '.o_form_view button[name="unlock"]',
            run() {
                // Waiting for the unlock button verifies the refreshed form.
            },
        },
    ],
});
