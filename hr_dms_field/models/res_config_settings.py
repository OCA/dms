# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    group_hr_public_dms = fields.Boolean(
        string="Show DMS Documents to logged employees",
        implied_group="hr_dms_field.group_hr_public_dms",
    )
