# Copyright 2023 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class DmsFile(models.Model):
    _inherit = "dms.file"

    def _prepare_ir_attachment_values(self):
        return {
            "dms_file_id": self.id,
            "name": self.name,
            "res_model": self.env.context.get("active_model"),
            "res_id": self.env.context.get("active_id"),
        }

    def action_create_attachment_from_record(self):
        return self.env["ir.attachment"].create(self._prepare_ir_attachment_values())
