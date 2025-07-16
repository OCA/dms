# Copyright 2025 Innovyou - Lorenzo Carta
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import io
import zipfile

from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.tools import human_size


class DmsFileDownloadWizard(models.TransientModel):
    _name = "dms.file.download.wizard"
    _description = "DMS File Download Wizard"

    name = fields.Char(string="Filename", default="dms_files.zip")
    file_ids = fields.Many2many("dms.file", string="Files")
    zip_file = fields.Binary(string="ZIP File", readonly=True, attachment=True)

    def action_download_zip(self):
        # Check size limit
        max_size_mb = int(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("dms_zip_download.max_size", default=100)
        )

        if max_size_mb > 0:
            total_size = sum(self.file_ids.mapped("size"))
            total_size_mb = total_size / (1024 * 1024)
            if total_size_mb > max_size_mb:
                error_msg = _(
                    "The total size of selected files (%(total_size)s) "
                    "exceeds the maximum allowed size of %(max_size)s MB.",
                    total_size=human_size(total_size),
                    max_size=max_size_mb,
                )
                raise UserError(error_msg)

        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for file in self.file_ids:
                file_content = file.with_context(bin_size=False).content
                if file_content:
                    file_name = file.name

                    # Handle duplicate filenames
                    file_counter = 1
                    original_name = file_name
                    while file_name in zip_file.namelist():
                        name_parts = original_name.rsplit(".", 1)
                        if len(name_parts) > 1:
                            file_name = (
                                f"{name_parts[0]}_{file_counter}.{name_parts[1]}"
                            )
                        else:
                            file_name = f"{original_name}_{file_counter}"
                        file_counter += 1

                    zip_file.writestr(file_name, base64.b64decode(file_content))

        zip_buffer.seek(0)
        self.zip_file = base64.b64encode(zip_buffer.read())
        url = f"/web/content/{self._name}/{self.id}/zip_file/{self.name}?download=true"
        return {
            "type": "ir.actions.act_url",
            "url": url,
            "target": "self",
        }
