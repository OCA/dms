# Copyright 2017-2019 MuK IT GmbH
# Copyright 2024 Subteno - Timothée Vannier (https://www.subteno.com).
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Document Management System",
    "summary": """Document Management System for Odoo""",
    "version": "17.0.1.2.0",
    "category": "Document Management",
    "license": "LGPL-3",
    "website": "https://github.com/OCA/dms",
    "author": "MuK IT, Tecnativa, Odoo Community Association (OCA)",
    "depends": [
        "mail",
        "http_routing",
        "onboarding",
        "portal",
        "base",
        "web",
    ],
    "data": [
        # Security
        "security/security.xml",
        "security/ir.model.access.csv",
        # Actions
        "actions/file.xml",
        # Templates
        "template/portal.xml",
        # Data
        "data/onboarding_data.xml",
        # Views
        "views/dms_tag.xml",
        "views/dms_category.xml",
        "views/dms_file.xml",
        "views/dms_directory.xml",
        "views/storage.xml",
        "views/dms_access_groups_views.xml",
        "views/res_config_settings.xml",
        "views/menu.xml",
        # Wizard
        "wizards/wizard_dms_file_move_views.xml",
        "wizards/wizard_dms_share_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            # Style
            "dms/static/src/scss/directory_kanban.scss",
            "dms/static/src/scss/file_kanban.scss",
            "dms/static/src/scss/dms_common.scss",
            # JS
            "dms/static/src/models/*.js",
            "dms/static/src/js/fields/path_json/path_owl.esm.js",
            "dms/static/src/js/fields/preview_binary/preview_record.esm.js",
            "dms/static/src/js/views/*.esm.js",
            # XML
            "dms/static/src/js/fields/path_json/path_owl.xml",
            "dms/static/src/js/fields/preview_binary/preview_record.xml",
            "dms/static/src/js/views/*.xml",
        ],
        "web.assets_frontend": [
            "dms/static/src/scss/portal.scss",
        ],
        "web.assets_tests": [
            "dms/static/tests/tours/**/*",
        ],
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
    "icon": "/dms/static/description/icon.png",
    "application": True,
}
