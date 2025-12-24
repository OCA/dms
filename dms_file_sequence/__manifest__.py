# Copyright 2025 APSL-Nagarro - Miquel Alzanillas, Antoni Marroig
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Dms File Sequence",
    "version": "17.0.1.0.1",
    "category": "Document Management",
    "website": "https://github.com/OCA/dms",
    "author": "APSL-Nagarro, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": ["dms"],
    "data": [
        "data/ir_sequence.xml",
        "views/dms_file_views.xml",
        "views/res_config_settings_view.xml",
    ],
    "installable": True,
    "maintainers": ["miquelalzanillas", "peluko00"],
    "post_init_hook": "post_init_hook",
}
