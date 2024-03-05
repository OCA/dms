# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class DmsAccessGroup(models.Model):
    _inherit = "dms.access.group"

    role_ids = fields.Many2many(
        comodel_name="res.users.role",
        relation="dms_access_group_user_roles_rel",
        column1="gid",
        column2="rid",
        string="Roles",
    )

    @api.depends("role_ids", "role_ids.users")
    def _compute_users(self):
        """Add the corresponding depends and the users of the roles."""
        res = super()._compute_users()
        for record in self.filtered("role_ids"):
            users = record.users
            users |= record.mapped("role_ids.users")
            record.update({"users": users, "count_users": len(users)})
        return res
