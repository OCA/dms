import re

from odoo import api, models


class IrAttachment(models.Model):

    _inherit = "ir.attachment"

    def _dms_file_name(self, directory_id, file_name):
        count = 1
        for file in directory_id.file_ids:

            dms_file_name = re.sub(r" \([0-9]*\)", "", file.name)
            if dms_file_name == file_name:
                count += 1

        file, ext = re.split(r"\.", file_name)
        return file + " ({}).".format(count) + ext if count > 1 else file_name

    def _create_record_dir(self, storage_id, attachment_id):
        dms_field = self.env["ir.module.module"].search([("name", "=", "dms_field")])

        directory_fields = {
            "name": attachment_id.res_name.replace("/", "-"),
            "is_root_directory": True,
            "parent_id": False,
            "root_storage_id": storage_id.id,
        }

        if dms_field and dms_field.state == "installed":
            directory_fields["res_id"] = attachment_id.res_id

        return self.env["dms.directory"].create(directory_fields)

    @api.model
    def create(self, vals):
        if "dms_file" in vals and vals["dms_file"]:
            del vals["dms_file"]
            return super(IrAttachment, self).create(vals)
        else:
            attachment_id = super(IrAttachment, self).create(vals)
            if "res_model" in vals:
                storage_id = self.env["dms.storage"].search(
                    [("model_id", "=", vals["res_model"])]
                )

                if storage_id and storage_id.save_type == "attachment":
                    record_directory = self.env["dms.directory"].search(
                        [("complete_name", "=", attachment_id.res_name)]
                    )
                    if not record_directory:
                        record_directory = self._create_record_dir(
                            storage_id, attachment_id
                        )

                    attachments_dir_id = record_directory.child_directory_ids.filtered(
                        lambda r: r.name == "Attachments"
                    )

                    if not attachments_dir_id:
                        attachments_dir_id = self.env["dms.directory"].create(
                            {
                                "name": "Attachments",
                                "parent_id": record_directory.id,
                                "storage_id": storage_id.id,
                                "record_ref": "{},{}".format(
                                    attachment_id.res_model, attachment_id.res_id
                                ),
                            }
                        )
                    file_name = self._dms_file_name(attachments_dir_id, vals["name"])

                    self.env["dms.file"].create(
                        {
                            "name": file_name,
                            "directory_id": attachments_dir_id.id,
                            "attachment_id": attachment_id.id,
                            "record_ref": "{},{}".format(
                                attachment_id.res_model, attachment_id.res_id
                            ),
                        }
                    )

            return attachment_id
