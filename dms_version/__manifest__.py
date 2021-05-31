# Copyright 2017-2020 MuK IT GmbH
# Copyright 2021 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Document Management System Version",
    "summary": """Version Control for Documents""",
    "version": "14.0.1.0.0",
    "category": "Document Management",
    "license": "LGPL-3",
    "website": "https://github.com/OCA/dms",
    "author": "MuK IT, Tecnativa, Odoo Community Association (OCA)",
    "depends": ["dms"],
    "external_dependencies": {"python": ["bsdiff4"]},
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/dms_file_view.xml",
        "views/dms_version_view.xml",
        "views/dms_storage_view.xml",
    ],
    "application": False,
}
