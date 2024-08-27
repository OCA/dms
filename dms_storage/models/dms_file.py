# Copyright 2022 CreuBlanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class DmsFile(models.Model):
    _inherit = "dms.file"

    storage_path = fields.Char()
    storage_backend_id = fields.Many2one("fs.storage")

    def _update_content_vals(self, vals, binary):
        result = super()._update_content_vals(vals, binary)
        result.update(
            {
                "storage_path": False,
                "storage_backend_id": False,
            }
        )
        if self.storage_id.save_type == "storage":
            storage_path = self.path_names
            if self.storage_path:
                self.storage_id.storage_backend_id.delete(self.storage_path)
            self.storage_id.storage_backend_id.add(storage_path, binary)
            result["storage_path"] = storage_path
            result["storage_backend_id"] = self.storage_id.storage_backend_id.id
        return result

    @api.depends("storage_path")
    def _compute_content(self):
        res = super()._compute_content()
        for record in self.filtered(lambda r: r.storage_path):
            record.content = self.storage_backend_id.get(
                record.storage_path, binary=False
            )
        return res
