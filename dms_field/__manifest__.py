# Copyright 2020 Creu Blanca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "DMS Field",
    "summary": """
        Create DMS View and allow to use them inside a record""",
    "version": "15.0.1.1.0",
    "license": "LGPL-3",
    "author": "Creu Blanca,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/dms",
    "depends": ["dms"],
    "data": [
        "views/dms_directory.xml",
        "views/dms_field_template_views.xml",
        "views/dms_storage.xml",
        "security/ir.model.access.csv",
        "security/security.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "dms_field/static/src/js/**/*",
            "dms_field/static/src/scss/**/*",
        ],
        "web.assets_qweb": ["dms_field/static/src/xml/**/*"],
    },
    "qweb": ["static/src/xml/*.xml"],
    "demo": ["demo/partner_dms.xml"],
}
