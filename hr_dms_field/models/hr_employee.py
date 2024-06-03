# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class HrEmployeeBase(models.AbstractModel):
    _name = "hr.employee.base"
    _inherit = ["hr.employee.base", "dms.field.mixin"]
