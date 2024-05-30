/** @odoo-module **/

// /** ********************************************************************************
//     Copyright 2024 Subteno - Timothée Vannier (https://www.subteno.com).
//     License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
//  **********************************************************************************/
import {registry} from "@web/core/registry";

registry.category("web_tour.tours").add("dms_portal_mail_tour", {
    url: "/my/dms",
    test: true,
    steps: () => [
        {
            content: "Go to Mails directory",
            extra_trigger: "li.breadcrumb-item:contains('Documents')",
            trigger: ".tr_dms_directory_link:contains('Mails')",
        },
        {
            content: "Go to Mail_01.eml",
            extra_trigger: "li.breadcrumb-item:contains('Mails')",
            trigger: ".tr_dms_file_link:contains('Mail_01.eml')",
        },
    ],
});

registry.category("web_tour.tours").add("dms_portal_partners_tour", {
    url: "/my/dms",
    test: true,
    steps: () => [
        {
            content: "Go to Partners directory",
            extra_trigger: "li.breadcrumb-item:contains('Documents')",
            trigger: ".tr_dms_directory_link:contains('Partners')",
        },
        {
            content: "Go to Joel Willis",
            extra_trigger: "li.breadcrumb-item:contains('Partners')",
            trigger: ".tr_dms_directory_link:contains('Joel Willis')",
        },
        {
            content: "Go to test.txt",
            extra_trigger: "li.breadcrumb-item:contains('Joel Willis')",
            trigger: ".tr_dms_file_link:contains('test.txt')",
        },
    ],
});
