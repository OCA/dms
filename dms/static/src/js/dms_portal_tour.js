odoo.define("dms.tour", function (require) {
    "use strict";

    var tour = require("web_tour.tour");

    tour.register(
        "dms_portal_tour",
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
                content: "Go to Documents directory",
                extra_trigger: "li.breadcrumb-item:contains('Documents')",
                trigger: ".tr_dms_directory_link:eq(0)",
            },
        ]
    );
});
