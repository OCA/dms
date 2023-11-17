# Copyright 2017-2019 MuK IT GmbH
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Document Management System",
    "summary": """Document Management System for Odoo""",
    "version": "16.0.1.0.2",
    "category": "Document Management",
    "license": "LGPL-3",
    "website": "https://github.com/OCA/dms",
    "author": "MuK IT, Tecnativa, Odoo Community Association (OCA)",
    "depends": [
        "mail",
        "http_routing",
        "portal",
        "base",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "actions/file.xml",
        "template/onboarding.xml",
        "views/menu.xml",
        "views/tag.xml",
        "views/category.xml",
        "views/dms_file.xml",
        "views/directory.xml",
        "views/storage.xml",
        "views/dms_access_groups_views.xml",
        "views/res_config_settings.xml",
        "views/dms_portal_templates.xml",
    ],
    "assets": {
        "mail.assets_messaging": [
            ("include", "mail.assets_core_messaging"),
            "dms/static/src/models/*.js",
        ],
        "web.assets_backend": [
            "dms/static/src/scss/*",
            "dms/static/src/js/fields/*",
            "dms/static/src/js/views/*.esm.js",
            "dms/static/src/js/views/*.xml",
            "dms/static/src/js/views/fields/binary/*",
        ],
        "web.assets_frontend": ["dms/static/src/js/dms_portal_tour.js"],
    },
    "demo": [
        "demo/res_users.xml",
        "demo/access_group.xml",
        "demo/category.xml",
        "demo/tag.xml",
        "demo/storage.xml",
        "demo/directory.xml",
        "demo/file.xml",
    ],
    "images": ["static/description/banner.png"],
    "application": True,
}
