# Copyright 2026 Ledo Enterprises
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

from ..models.dms_file import SPREADSHEET_MIMETYPE


class DmsSpreadsheetCreate(models.TransientModel):
    """Wizard to create a new spreadsheet inside a DMS directory."""

    _name = "dms.spreadsheet.create"
    _description = "Create Spreadsheet in DMS"

    name = fields.Char(
        string="Spreadsheet Name", required=True, default="New Spreadsheet"
    )
    directory_id = fields.Many2one(
        comodel_name="dms.directory",
        string="Directory",
        required=True,
        domain="[('permission_create', '=', True)]",
    )

    def action_create_spreadsheet(self):
        self.ensure_one()
        file = self.env["dms.file"].create(
            {
                "name": self.name,
                "directory_id": self.directory_id.id,
                "mimetype": SPREADSHEET_MIMETYPE,
            }
        )
        return file.open_spreadsheet()
