// /** ********************************************************************************
//     Copyright 2024 Subteno - Timothée Vannier (https://www.subteno.com).
//     License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
//  **********************************************************************************/
import {registry} from "@web/core/registry";

registry.category("web_tour.tours").add("dms_portal_mail_tour", {
    url: "/my/dms",
    steps: () => [
        {
            content: "Go to Mails directory",
            trigger: ".tr_dms_directory_link:contains('Mails')",
            run: "click",
            expectUnloadPage: true,
        },
        {
            content: "Mail_01.eml is reachable",
            trigger: ".tr_dms_file_link:contains('Mail_01.eml')",
        },
    ],
});

registry.category("web_tour.tours").add("dms_portal_partners_tour", {
    url: "/my/dms",
    steps: () => [
        {
            content: "Go to Partners directory",
            trigger: ".tr_dms_directory_link:contains('Partners')",
            run: "click",
            expectUnloadPage: true,
        },
        {
            content: "Go to Joel Willis",
            trigger: ".tr_dms_directory_link:contains('Joel Willis')",
            run: "click",
            expectUnloadPage: true,
        },
        {
            content: "test.txt is reachable",
            trigger: ".tr_dms_file_link:contains('test.txt')",
        },
    ],
});
