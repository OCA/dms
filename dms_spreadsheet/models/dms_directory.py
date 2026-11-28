# Copyright 2026 Ledo Enterprises
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class DmsDirectory(models.Model):
    _inherit = "dms.directory"

    def action_new_spreadsheet(self):
        """Open the New Spreadsheet wizard pre-filled with this directory."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "New Spreadsheet",
            "res_model": "dms.spreadsheet.create",
            "view_mode": "form",
            "target": "new",
            "context": {"default_directory_id": self.id},
        }
