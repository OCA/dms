# Copyright 2023 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Dms Attachment Link",
    "version": "15.0.1.0.0",
    "category": "Document Management",
    "website": "https://github.com/OCA/dms",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": ["dms"],
    "data": [
        "views/dms_file_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "dms_attachment_link/static/src/js/dms_attachment_link.esm.js",
        ],
        "web.assets_qweb": [
            "dms_attachment_link/static/src/xml/chatter.xml",
        ],
    },
    "installable": True,
    "maintainers": ["victoralmau"],
}
