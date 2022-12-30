odoo.define("dms.tour", function (require) {
    "use strict";

    var tour = require("web_tour.tour");

    tour.register(
        "dms_portal_mail_tour",
        {
            test: true,
            url: "/my",
        },
        [
            {
                content: "Go /my/dms url",
                trigger: 'a[href*="/my/dms"]',
            },
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
        ]
    );
    tour.register(
        "dms_portal_partners_tour",
        {
            test: true,
            url: "/my",
        },
        [
            {
                content: "Go /my/dms url",
                trigger: 'a[href*="/my/dms"]',
            },
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
        ]
    );
    return {};
});
