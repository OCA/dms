# Copyright (C) 2024 Cetmix OÜ
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


{
    "name": "DMS Partner related attachments Link",
    "summary": """
        This module adds a button to the Partner form, linking to
        related files stored in the attachment storage.
    """,
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Cetmix, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/dms",
    "depends": ["dms"],
    "data": [
        "views/res_partner_views.xml",
    ],
}
