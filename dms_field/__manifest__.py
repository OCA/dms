# Copyright 2020 Creu Blanca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "DMS Field",
    "summary": """
        Create DMS View and allow to use them inside a record""",
    "version": "16.0.1.1.2",
    "license": "LGPL-3",
    "author": "Creu Blanca,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/dms",
    "depends": ["dms"],
    "data": [
        "views/dms_access_group_views.xml",
        "views/dms_directory.xml",
        "views/dms_field_template_views.xml",
        "views/dms_storage.xml",
        "security/ir.model.access.csv",
        "security/security.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "dms_field/static/src/**/*",
            ("remove", "dms_field/static/src/views/fields/x2many/x2many_field.xml"),
            (
                "after",
                "/web/static/src/views/fields/x2many/x2many_field.xml",
                "dms_field/static/src/views/fields/x2many/x2many_field.xml",
            ),
        ],
    },
    "demo": ["demo/partner_dms.xml"],
}
