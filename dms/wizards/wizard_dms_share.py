# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class WizardDmsShare(models.TransientModel):
    _name = "wizard.dms.share"
    _inherit = "portal.share"
    _description = "Wizard for sharing DMS records"

    @api.model
    def _selection_target_model(self):
        return [
            (model.model, model.name)
            for model in self.env["ir.model"]
            .sudo()
            .search([("model", "in", ("dms.directory", "dms.file"))])
        ]
