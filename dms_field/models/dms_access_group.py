# Copyright 2024 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class DmsAccessGroups(models.Model):
    _inherit = "dms.access.group"

    model_ref = fields.Reference(
        selection="_selection_reference_value",
        string="Default value",
    )

    @api.model
    def _selection_reference_value(self):
        models = (
            self.env["ir.model"]
            .sudo()
            .search([("transient", "=", False)], order="name asc")
        )
        return [(model.model, model.name) for model in models]
