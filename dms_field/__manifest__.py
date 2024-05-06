# Copyright 2020 Creu Blanca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "DMS Field",
    "summary": """
        Create DMS View and allow to use them inside a record""",
    "version": "15.0.1.0.0",
    "license": "LGPL-3",
    "author": "Creu Blanca,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/dms",
    "depends": ["dms"],
    "data": [
        "wizards/dms_add_directory_record.xml",
        "views/dms_storage.xml",
        "views/dms_directory.xml",
        "security/ir.model.access.csv",
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
