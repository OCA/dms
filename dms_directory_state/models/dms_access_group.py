# Copyright 2026 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class DmsAccessGroup(models.Model):
    _inherit = "dms.access.group"

    perm_change_state = fields.Boolean(
        string="Can Change Directory State",
        help="This Group is allowed to change the State of a Directory.",
    )
