# Copyright 2025 APSL-Nagarro - Miquel Alzanillas, Antoni Marroig
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    dms_file_display_name_pattern = fields.Char(
        config_parameter="dms_file_sequence.display_name_pattern",
        default="%(sequence_code)s - %(name)s",
        help=(
            "Use %(sequence_code)s and %(name)s to include the sequence code "
            "and the name of the file in the display name."
        ),
    )
