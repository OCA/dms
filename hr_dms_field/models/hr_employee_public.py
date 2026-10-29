# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class HrEmployeePublic(models.Model):
    """The field dms_directory_ids must exist in this model too, as hr.employee
    reads its public fields from here when the user is not an HR officer."""

    _name = "hr.employee.public"
    _inherit = ("hr.employee.public", "dms.field.mixin")

    is_logged = fields.Boolean(compute="_compute_is_logged")

    @api.depends("user_id")
    @api.depends_context("uid")
    def _compute_is_logged(self):
        for record in self:
            record.is_logged = record.user_id == self.env.user
