# Copyright 2026 Windweaver
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class ProjectProject(models.Model):
    _name = "project.project"
    _inherit = ["project.project", "dms.field.mixin"]
