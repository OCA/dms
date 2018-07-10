###################################################################################
# 
#    Copyright (C) 2017 MuK IT GmbH
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###################################################################################

from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    
    _inherit = 'res.config.settings'
    
    module_muk_dms_access = fields.Boolean(
        string="Access Control",
        help="Allows the creation of groups to define access rights.")
    
    module_muk_dms_widget = fields.Boolean(
        string="Binary Widget Support",
        help="Allows the user to use DMS documents as input for any binary field.")
    
    module_muk_archive = fields.Boolean(
        string="Download Directories",
        help="Allows to download directories as a archive file.")
    
    module_muk_dms_thumbnails = fields.Boolean(
        string="Automatic Thumbnails",
        help="Allows the creation of thumbnails for files.")
    
    module_muk_dms_export = fields.Boolean(
        string="Export Files",
        help="Allows the conversion of existing files.")
    
    module_muk_dms_attachment = fields.Boolean(
        string="Attachment Storage Location",
        help="Allows attachments to be stored inside of MuK Documents.")

    module_muk_dms_attachment_rules = fields.Boolean(
        string="Attachment Storage Rules",
        help="Allows attachments to be automatically placed in the right directory.")
    
    module_muk_dms_attachment_automation = fields.Boolean(
        string="Attachment Rule Automation",
        help="Allows you to create rule templates to create attachment rules.")
    
    module_muk_dms_attachment_wizard = fields.Boolean(
        string="Attachment Wizard",
        help="Allows documents to be used as attachments.")
    
    module_muk_dms_finder = fields.Boolean(
        string="Finder",
        help="Enables the Document Finder.")
    
    module_muk_dms_file = fields.Boolean(
        string="File Store",
        help="Enables a new save option to store files into a file store.")
    
    module_muk_dms_lobject = fields.Boolean(
        string="Large Objects ",
        help="Enables a new save option to store files into large objects.")
    
    max_upload_size = fields.Integer(
        string="Size",
        help="Defines the maximum upload size in MB. Default (25MB)")
    
    forbidden_extensions = fields.Char(
        string="Extensions",
        help="Defines a list of forbidden file extensions. (Example: '.exe,.msi')")
    
    @api.multi
    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        param = self.env['ir.config_parameter'].sudo()
        param.set_param('muk_dms.max_upload_size', self.max_upload_size)
        param.set_param('muk_dms.forbidden_extensions', self.forbidden_extensions)
        return res

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(
            max_upload_size=int(params.get_param('muk_dms.max_upload_size', default=25)),
            forbidden_extensions=params.get_param('muk_dms.forbidden_extensions', default=""),
        )
        return res
