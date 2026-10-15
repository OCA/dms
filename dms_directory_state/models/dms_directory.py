# Copyright 2026 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import exceptions, fields, models

DIRECTORY_STATES = [
    ("draft", "In Development"),
    ("released", "Released"),
    ("obsolete", "Obsolete"),
]


class DmsDirectory(models.Model):
    _inherit = "dms.directory"

    state = fields.Selection(
        selection=DIRECTORY_STATES,
        default="draft",
        tracking=True,
    )

    def _build_state_permission_error(self):
        return self.env._(
            "You are not allowed to change the state of %(dir_names)s.",
            dir_names=", ".join(self.mapped("display_name")),
        )

    def _check_state_permission(self):
        if dirs_without_permissions := self.filtered(
            lambda d: not any(
                g
                for g in d.complete_group_ids
                if g.perm_write and g.perm_change_state and self.env.user in g.users
            )
        ):
            raise exceptions.AccessError(
                dirs_without_permissions._build_state_permission_error()
            )

    def write(self, vals):
        if "state" in vals.keys() and not self.env.su:
            self._check_state_permission()
        return super().write(vals)
