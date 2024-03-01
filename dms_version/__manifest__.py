# Copyright 2017-2020 MuK IT GmbH
# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Document Management System Version",
    "summary": """Version Control for Documents""",
    "version": "14.0.1.0.0",
    "category": "Document Management",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/dms",
    "author": """MuK IT,
               Tecnativa,
               elego Software Solutions Gmbh,
               Odoo Community Association (OCA)""",
    "depends": ["dms", "base_revision"],
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "wizard/restore_old_revision_view.xml",
        "views/dms_file_view.xml",
        "views/dms_directory_view.xml",
        "views/dms_storage_view.xml",
    ],
    "maintainers": ["victoralmau"],
    "application": False,
}
