# Copyright 2023 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class WizardIrAttachmentDmsFile(models.TransientModel):
    _name = "wizard.ir.attachment.dms.file"
    _description = "Wizard Ir Attachment DMS File"

    dms_file_id = fields.Many2one(
        comodel_name="dms.file", string="DMS File", required=True
    )

    def _prepare_ir_attachment_values(self):
        return {
            "dms_file_id": self.dms_file_id.id,
            "name": self.dms_file_id.name,
            "res_model": self.env.context.get("active_model"),
            "res_id": self.env.context.get("active_id"),
        }

    def action_link(self):
        self.env["ir.attachment"].create(self._prepare_ir_attachment_values())
