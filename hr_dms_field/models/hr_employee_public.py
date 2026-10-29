# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class HrEmployeePublic(models.Model):
    """The field dms_directory_ids must exist in this model too, as hr.employee
    reads its public fields from here when the user is not an HR officer."""

    _name = "hr.employee.public"
    _inherit = ("hr.employee.public", "dms.field.mixin")
