# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class WizardDmsFileMove(models.TransientModel):
    _name = "wizard.dms.file.move"
    _description = "Wizard Dms File Move"

    count_files = fields.Integer(readonly=True)
    directory_id = fields.Many2one(
        comodel_name="dms.directory", required=True, string="Directory"
    )

    @api.model
    def default_get(self, fields):
        vals = super().default_get(fields)
        if self.env.context.get("active_ids"):
            vals.update({"count_files": len(self.env.context.get("active_ids"))})
        return vals

    def process(self):
        items = self.env["dms.file"].browse(self.env.context.get("active_ids"))
        items.write({"directory_id": self.directory_id})
