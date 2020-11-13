# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import api, models


class IrAttachment(models.Model):

    _inherit = "ir.attachment"

    def _get_dms_directories(self, res_model, res_id):
        return self.env["dms.directory"].search(
            [("res_model", "=", res_model), ("res_id", "=", res_id)]
        )

    def _dms_directories_create(self):
        items = self._get_dms_directories(self.res_model, False)
        for item in items:
            model_item = self.env[self.res_model].sudo().browse(self.res_id)
            ir_model_item = self.env["ir.model"].search(
                [("model", "=", self.res_model)]
            )
            self.env["dms.directory"].create(
                {
                    "name": model_item.display_name,
                    "model_id": ir_model_item.id,
                    "res_model": self.res_model,
                    "res_id": self.res_id,
                    "parent_id": item.id,
                    "storage_id": item.storage_id.id,
                }
            )

    def _dms_operations(self):
        for attachment in self:
            if not attachment.res_model or not attachment.res_id:
                continue
            directories = self._get_dms_directories(
                attachment.res_model, attachment.res_id
            )
            if not directories:
                attachment._dms_directories_create()
                # Get dms_directories again (with items previously created)
                directories = self._get_dms_directories(
                    attachment.res_model, attachment.res_id
                )
            # Auto-create_files
            for directory in directories:
                self.env["dms.file"].create(
                    {
                        "name": attachment.name,
                        "directory_id": directory.id,
                        "attachment_id": attachment.id,
                        "res_model": attachment.res_model,
                        "res_id": attachment.res_id,
                    }
                )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if not self.env.context.get("dms_file"):
            records._dms_operations()
        return records
