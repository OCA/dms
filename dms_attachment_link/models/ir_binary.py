# Copyright 2024 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models


class IrBinary(models.AbstractModel):
    _inherit = "ir.binary"

    def _record_to_stream(self, record, field_name):
        """We need to overwrite for the download and preview to be correct."""
        if record._name == "ir.attachment" and record.dms_file_id:
            record = record.dms_file_id
            field_name = "content"
        return super()._record_to_stream(record=record, field_name=field_name)
