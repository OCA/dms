# Copyright 2020 Creu Blanca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class DmsAddDirectory(models.TransientModel):
    _name = "dms.add.directory.record"
    _description = "Add Directory to a DMS Record"

    res_id = fields.Integer()
    res_model = fields.Char()
    storage_ids = fields.Many2many(
        "dms.storage", store=False, string="Possible storages"
    )
    storage_id = fields.Many2one("dms.storage", required=True)

    def create_directory(self):
        self.ensure_one()
        return self._create_directory().ids

    def _create_directory(self):
        return self.env["dms.directory"].create(self._create_directory_vals())

    def _create_directory_vals(self):
        record = self.env[self.res_model].browse(self.res_id)
        return {
            "storage_id": self.storage_id.id,
            "res_id": self.res_id,
            "res_model": self.res_model,
            "is_root_directory": True,
            "name": record.display_name,
            "group_ids": [(4, self.storage_id.field_default_group_id.id)],
        }
