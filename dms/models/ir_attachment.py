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

    @api.model
    def create(self, vals):
        if "dms_file" in vals and vals["dms_file"]:
            del vals["dms_file"]
            return super(IrAttachment, self).create(vals)
        else:
            attachment_id = super(IrAttachment, self).create(vals)
            if 'res_model' in vals:
                directory_id = self.env["dms.directory"].search(
                    [("ir_model_id", "=", vals["res_model"])]
                )

            if directory_id and directory_id.record_sub_directory:
                save_directory_id = self.env["dms.directory"].search(
                    [("name", "=", attachment_id.res_name.replace("/", "-"))]
                )
                if not save_directory_id:
                    save_directory_id = self.env["dms.directory"].create(
                        {
                            "name": attachment_id.res_name.replace("/", "-"),
                            "parent_id": directory_id.id,
                            "storage_id": directory_id.root_storage_id.id,
                            "record_ref": "{},{}".format(
                                attachment_id.res_model, attachment_id.res_id
                            ),
                        }
                    )

                file_name = self._dms_file_name(save_directory_id, vals["name"])

                self.env["dms.file"].create(
                    {
                        "name": file_name,
                        "directory_id": save_directory_id.id,
                        "attachment_id": attachment_id.id,
                        "record_ref": "{},{}".format(
                            attachment_id.res_model, attachment_id.res_id
                        ),
                    }
                )

            elif directory_id:

                file_name = self._dms_file_name(directory_id, vals["name"])

                self.env["dms.file"].create(
                    {
                        "name": file_name,
                        "directory_id": directory_id.id,
                        "attachment_id": attachment_id.id,
                        "record_ref": "{},{}".format(
                            attachment_id.res_model, attachment_id.res_id
                        ),
                    }
                )

            return attachment_id
