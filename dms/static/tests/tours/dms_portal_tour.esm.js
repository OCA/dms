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
            trigger: ".tr_dms_directory_link:contains('Mails')",
            run: "click",
        },
        {
            trigger: ".tr_dms_file_link:contains('Mail_01.eml')",
        },
    ],
});

registry.category("web_tour.tours").add("dms_portal_partners_tour", {
    url: "/my/dms",
    test: true,
    steps: () => [
        {
            trigger: ".tr_dms_directory_link:contains('Mails')",
            run: "click",
        },
        {
            trigger: ".tr_dms_file_link:contains('Mail_01.eml')",
        },
    ],
});
