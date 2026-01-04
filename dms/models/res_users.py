# Copyright 2024 Subteno - Timothée Vannier (https://www.subteno.com).
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    dms_access_group_ids = fields.Many2many(
        comodel_name="dms.access.group",
        relation="dms_access_group_explicit_users_rel",
        column1="uid",
        column2="gid",
        string="DMS Access Groups",
        help="Assign this user to DMS access groups for specific directory permissions.",
    )
