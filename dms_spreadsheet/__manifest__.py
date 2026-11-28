# Copyright 2026 Ledo Enterprises
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "DMS Spreadsheet",
    "summary": "Create and edit spreadsheets directly within the DMS file manager",
    "version": "18.0.1.0.0",
    "category": "Document Management",
    "license": "AGPL-3",
    "author": "Ledo Enterprises, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/dms",
    "depends": [
        "dms",
        "spreadsheet_oca",
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizard/dms_spreadsheet_create_views.xml",
        "views/dms_file_views.xml",
        "views/dms_directory_views.xml",
    ],
    "installable": True,
    "auto_install": False,
}
