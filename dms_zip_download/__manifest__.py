# Copyright 2025 Innovyou - Lorenzo Carta
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "DMS Zip Download",
    "version": "18.0.1.0.0",
    "category": "Document Management",
    "website": "https://github.com/OCA/dms",
    "author": "Innovyou, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": ["dms"],
    "installable": True,
    "data": [
        "security/ir.model.access.csv",
        "data/server_actions.xml",
        "views/res_config_settings_views.xml",
    ],
    "maintainers": ["LorenzoC0"],
}
