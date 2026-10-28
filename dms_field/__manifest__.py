# Copyright 2020 Creu Blanca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "DMS Field",
    "summary": "Create DMS View and allow to use them inside a record",
    "version": "20.0.1.0.0",
    "license": "LGPL-3",
    "author": "Creu Blanca,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/dms",
    "depends": ["dms"],
    "data": [
        "views/dms_access_group_views.xml",
        "views/dms_directory.xml",
        "views/dms_field_template_views.xml",
        "views/dms_storage.xml",
        "security/ir.access.csv",
        "data/assets.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "dms_field/static/src/**/*",
            ("remove", "dms_field/static/src/views/fields/x2many/x2many_field.xml"),
        ],
        "web.assets_unit_tests": [
            "dms_field/static/tests/**/*",
            ("remove", "dms_field/static/tests/tours/**/*"),
        ],
        "web.assets_tests": [
            "dms_field/static/tests/tours/**/*",
        ],
    },
    "demo": ["demo/partner_dms.xml"],
    "maintainers": ["CarlosRoca13"],
}
