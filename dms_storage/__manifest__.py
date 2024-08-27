# Copyright 2022 CreuBlanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Dms Storage",
    "summary": """
        Integrate DMS with external Storages""",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    "author": "CreuBlanca,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/dms",
    "depends": ["dms", "fs_storage"],
    "data": [
        "views/dms_storage.xml",
    ],
}
