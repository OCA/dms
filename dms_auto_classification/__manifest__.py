# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Auto classify documents into DMS",
    "version": "16.0.1.0.0",
    "category": "Document Management",
    "website": "https://github.com/OCA/dms",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": ["dms"],
    "installable": True,
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "views/dms_classification_template_views.xml",
        "wizards/wizard_dms_classification_views.xml",
    ],
    "demo": ["demo/dms_classification_template_demo.xml"],
    "maintainers": ["victoralmau"],
}
