# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import api, models


class IrAttachment(models.Model):

    _inherit = "ir.attachment"

    def _get_dms_directories(self, res_model, res_id):
        domain = [
            ("res_model", "=", res_model),
            ("res_id", "=", res_id),
            ("storage_id.save_type", "=", "attachment"),
        ]
        if self.env.context.get("attaching_to_record"):
            domain += [("storage_id.include_message_attachments", "=", True)]
        return self.env["dms.directory"].search(domain)

    def _dms_directories_create(self):
        items = self._get_dms_directories(self.res_model, False)
        for item in items:
            model_item = self.env[self.res_model].browse(self.res_id)
            ir_model_item = self.env["ir.model"].search(
                [("model", "=", self.res_model)]
            )
            self.env["dms.directory"].sudo().with_context(check_name=False).create(
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
            if (
                attachment.type != "binary"
                or not attachment.res_model
                or not attachment.res_id
            ):
                continue
            directories = attachment._get_dms_directories(
                attachment.res_model, attachment.res_id
            )
            if not directories:
                attachment._dms_directories_create()
                # Get dms_directories again (with items previously created)
                directories = attachment._get_dms_directories(
                    attachment.res_model, attachment.res_id
                )
            # Auto-create_files (if not exists)
            for directory in directories:
                dms_file_model = self.env["dms.file"].sudo()
                dms_file = dms_file_model.search(
                    [
                        ("attachment_id", "=", attachment.id),
                        ("directory_id", "=", directory.id),
                    ]
                )
                if not dms_file:
                    dms_file_model.create(
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

    def write(self, vals):
        res = super().write(vals)
        if not self.env.context.get("dms_file") and self.env.context.get(
            "attaching_to_record"
        ):
            self._dms_operations()
        return res
