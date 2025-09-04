# Copyright 2024 Tecnativa - Carlos Roca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Web Editor Media Dialog DMS",
    "summary": "Integrate DMS with media dialog of web editor",
    "version": "18.0.1.0.1",
    "license": "AGPL-3",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/dms",
    "depends": ["dms", "web_editor"],
    "assets": {
        "html_editor.assets_media_dialog": [
            "web_editor_media_dialog_dms/static/src/media_dialog/*",
        ]
    },
}
