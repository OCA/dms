from odoo import api, models, fields, tools


class IrAttachment(models.Model):

    _inherit = "ir.attachment"

    @api.model
    def create(self, vals):
        attachment_id = super(IrAttachment, self).create(vals)
        category_id = self.env['dms.directory'].search([
            ('ir_model_id', '=', vals['res_model'])])

        if category_id:
            self.env['dms.file'].create({
                'name': vals['name'],
                'directory_id': category_id.id,
                'attachment_id': attachment_id.id,
            })

        return attachment_id
