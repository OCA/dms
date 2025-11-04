# Copyright 2025 Kencove (https://www.kencove.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Document Management System Import",
    "summary": """
        Import data from document EE to dms CE
    """,
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "category": "Document Management",
    "author": "Kencove, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/dms",
    "depends": ["dms"],
    "external_dependencies": {"python": ["pathvalidate", "openupgradelib"]},
    "post_init_hook": "post_init_hook",
    "post_load": "post_load_hook",
    "uninstall_hook": "uninstall_hook",
}
