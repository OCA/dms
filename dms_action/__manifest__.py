# Copyright 2022 CreuBlanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Dms Action",
    "summary": """
        Allow to add actions on DMS""",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "CreuBlanca,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/dms",
    "depends": ["dms", "base_sparse_field"],
    "data": [
        "security/ir.model.access.csv",
        "views/dms_file.xml",
        "views/dms_directory.xml",
        "views/dms_action.xml",
        "template/assets.xml",
    ],
    "qweb": ["static/src/xml/dms_action_widget.xml"],
    "demo": [
        "demo/dms_action.xml",
    ],
}
