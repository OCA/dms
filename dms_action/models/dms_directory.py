# Copyright 2022 CreuBlanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class DmsDirectory(models.Model):
    _inherit = "dms.directory"

    dms_action_ids = fields.Many2many("dms.action")
