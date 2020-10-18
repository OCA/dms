# Copyright 2017-2020 MuK IT GmbH
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Document Management System Version",
    "summary": """Version Control for Documents""",
    "version": "13.0.1.0.0",
    "category": "Document Management",
    "license": "LGPL-3",
    "website": "http://github.com/OCA/dms",
    "author": "MuK IT,Odoo Community Association (OCA)",
    "depends": ["dms"],
    "data": [
        "security/ir.model.access.csv",
        "views/file.xml",
        "views/version.xml",
        "views/storage.xml",
    ],
    "application": False,
}
