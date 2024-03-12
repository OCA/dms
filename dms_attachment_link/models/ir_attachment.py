# Copyright 2023 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    dms_file_id = fields.Many2one(comodel_name="dms.file")

    @api.depends("dms_file_id.content")
    def _compute_datas(self):
        """Get the contents of the attachment directly from the DMS fiel."""
        _self = self.filtered("dms_file_id")
        res = super(IrAttachment, (self - _self))._compute_datas()
        for item in _self:
            item.datas = item.dms_file_id.content
        return res

    @api.model_create_multi
    def create(self, vals_list):
        """Create attachments and link them to DMS files."""
        attachments = super().create(vals_list)
        for attachment, vals in zip(attachments, vals_list):
            if "dms_file_id" in vals:
                attachment.datas = attachment.dms_file_id.content
        return attachments
