odoo.define("dms.tour", function(require) {
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
                content: "Go to Photos directory",
                trigger: ".tr_dms_directory_link:eq(1)",
            },
        ]
    );
    return {};
});
