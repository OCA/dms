# Copyright 2025 Innovyou - Lorenzo Carta
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    dms_zip_download_max_size = fields.Integer(
        string="ZIP Download Size Limit",
        config_parameter="dms_zip_download.max_size",
        default=100,
    )
