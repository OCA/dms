odoo.define("dms.tour", function(require) {
    "use strict";

    var tour = require("web_tour.tour");
    var base = require("web_editor.base");

    tour.register(
        "dms_portal_tour",
        {
            test: true,
            url: "/my",
            wait_for: base.ready(),
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
