# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrEmployeePublic(models.Model):
    _inherit = "hr.employee.public"

    is_logged = fields.Boolean(compute="_compute_is_logged", store=False)

    def _compute_is_logged(self):
        self.is_logged = False
        for record in self:
            if self.env.user == record.user_id:
                record.is_logged = True
