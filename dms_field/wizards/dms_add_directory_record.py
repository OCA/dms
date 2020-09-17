# Copyright 2020 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class DmsAddDirectory(models.TransientModel):
    _name = "dms.add.directory.record"
    _description = "Add Directory to a DMS Record"

    res_id = fields.Integer()
    storage_ids = fields.Many2many(
        "dms.storage", store=False, string="Possible storages"
    )
    storage_id = fields.Many2one("dms.storage", required=True)

    def create_directory(self):
        self.ensure_one()
        record = self.env[self.storage_id.model_id.model].browse(self.res_id)
        already_created = self.env["dms.directory"].search(
            [("name", "=", record.display_name)]
        )
        if already_created:
            return
        return self._create_directory().ids

    def _create_directory(self):
        return self.env["dms.directory"].create(self._create_directory_vals())

    def _create_directory_vals(self):
        record = self.env[self.storage_id.model_id.model].browse(self.res_id)
        return {
            "root_storage_id": self.storage_id.id,
            "res_id": self.res_id,
            "is_root_directory": True,
            "name": record.display_name,
        }
