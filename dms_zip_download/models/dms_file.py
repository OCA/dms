# Copyright 2025 Innovyou - Lorenzo Carta
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class DmsFile(models.Model):
    _inherit = "dms.file"

    def action_download_as_zip(self):
        wizard = self.env["dms.file.download.wizard"].create(
            {
                "file_ids": [(6, 0, self.ids)],
            }
        )
        return wizard.action_download_zip()
