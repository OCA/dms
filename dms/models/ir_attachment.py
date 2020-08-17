from odoo import api, models, fields, tools


class IrAttachment(models.Model):

    _inherit = "ir.attachment"

    @api.model
    def create(self, vals):
        attachment_id = super(IrAttachment, self).create(vals)
        directory_id = self.env['dms.directory'].search([
            ('ir_model_id', '=', vals['res_model'])])

        if directory_id and directory_id.record_sub_directory:
            save_directory_id = self.env['dms.directory'].search([
                ('name', '=', attachment_id.res_name)])
            if not save_directory_id:
                save_directory_id = self.env['dms.directory'].create({
                    'name': attachment_id.res_name.replace('/','-'),
                    'parent_id': directory_id.id,
                    'storage_id': directory_id.root_storage_id.id,
                })

            self.env['dms.file'].create({
                'name': vals['name'],
                'directory_id': save_directory_id.id,
                'attachment_id': attachment_id.id,
                'record_ref': "{},{}".format(
                    attachment_id.res_model, attachment_id.res_id),
            })

        elif directory_id:
            self.env['dms.file'].create({
                'name': vals['name'],
                'directory_id': directory_id.id,
                'attachment_id': attachment_id.id,
                'record_ref': "{},{}".format(
                    attachment_id.res_model, attachment_id.res_id),
            })

        return attachment_id
