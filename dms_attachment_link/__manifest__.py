# Copyright 2023 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Dms Attachment Link",
    "version": "13.0.1.1.0",
    "category": "Document Management",
    "website": "https://github.com/OCA/dms",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": ["dms"],
    "data": [
        "views/assets.xml",
        "views/dms_file_views.xml",
    ],
    "qweb": ["static/src/xml/chatter.xml"],
    "installable": True,
    "maintainers": ["victoralmau"],
}
