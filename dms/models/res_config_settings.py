###################################################################################
#
#    Copyright (c) 2017-2019 MuK IT GmbH.
#
#    This file is part of MuK Documents 
#    (see https://mukit.at).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
###################################################################################

from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    
    _inherit = 'res.config.settings'
    
    #----------------------------------------------------------
    # Base Addons
    #----------------------------------------------------------
    
    module_muk_dms_access = fields.Boolean(
        string="Access Control",
        help="Allows the creation of groups to define access rights.")
    
    module_muk_dms_mail = fields.Boolean(
        string="Mail Support",
        help="Adds support for messages and activities on directories and files.")
    
    module_muk_dms_version = fields.Boolean(
        string="Versioning",
        help="Enables version control for files.")
    
    module_muk_dms_trash = fields.Boolean(
        string="Restore Files",
        help="Activates a file trash to restore deleted files.")
    
    module_muk_dms_widget = fields.Boolean(
        string="Binary Widget Support",
        help="Allows the user to use documents as input for any binary field.")
    
    module_muk_archive = fields.Boolean(
        string="Download Directories",
        help="Allows to download directories as a archive file.")
    
    module_muk_dms_thumbnails = fields.Boolean(
        string="File Thumbnails",
        help="Automatically create file thumbnails based on the content.")
    
    module_muk_dms_index = fields.Boolean(
        string="File Indexation",
        help="Automatically create a file index based on the content.")
    
    #----------------------------------------------------------
    # Views
    #----------------------------------------------------------
    
    module_muk_dms_preview = fields.Boolean(
        string="File Preview",
        help="Activates the preview function on files.")
    
    module_muk_dms_view = fields.Boolean(
        string="Tree View",
        help="Activates the documents tree view.")
    
    module_muk_dms_finder = fields.Boolean(
        string="Finder",
        help="Enables the Document Finder.")
    
    #----------------------------------------------------------
    # Storage Addons
    #----------------------------------------------------------
    
    module_muk_dms_lobject = fields.Boolean(
        string="Large Objects Storage",
        help="Enables a new save option to store files into large objects.")
    
    module_muk_dms_file = fields.Boolean(
        string="Filestore Storage",
        help="Enables a new save option to store files into a filestore.")
    
    #----------------------------------------------------------
    # Attachment Addons
    #----------------------------------------------------------
    
    module_muk_dms_attachment = fields.Boolean(
        string="Documents Storage Location",
        help="Allows attachments to be stored inside of Documents.")

    module_muk_dms_attachment_rules = fields.Boolean(
        string="Documents Storage Rules",
        help="Allows attachments to be automatically placed in the right directory.")
    
    module_muk_dms_attachment_automation = fields.Boolean(
        string="Attachment Rule Automation",
        help="Allows you to create rule templates to create attachment rules.")
    
    module_muk_dms_attachment_wizard = fields.Boolean(
        string="Attachment Wizard",
        help="Allows documents to be used as attachments.")
    
    #----------------------------------------------------------
    # Integrations
    #----------------------------------------------------------
    
    module_muk_dms_actions = fields.Boolean(
        string="Document Actions",
        help="Create custom file operations.")
    
    module_muk_dms_users = fields.Boolean(
        string="Personal Documents",
        help="Automatic creation of user directories.")
    
    #----------------------------------------------------------
    # ... Addons
    #----------------------------------------------------------
    

    
    module_muk_dms_thumbnails = fields.Boolean(
        string="Automatic Thumbnails",
        help="Allows the creation of thumbnails for files.")
    
    module_muk_dms_export = fields.Boolean(
        string="Export Files",
        help="Allows the conversion of existing files.")
    
    #----------------------------------------------------------
    # Database
    #----------------------------------------------------------
    
    documents_binary_max_size = fields.Integer(
        string="Size",
        help="Defines the maximum upload size in MB. Default (25MB)")
    
    documents_forbidden_extensions = fields.Char(
        string="Extensions",
        help="Defines a list of forbidden file extensions. (Example: 'exe,msi')")
    
    #----------------------------------------------------------
    # Functions
    #----------------------------------------------------------
    
    @api.multi
    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        param = self.env['ir.config_parameter'].sudo()
        param.set_param('muk_web_utils.binary_max_size', self.documents_binary_max_size)
        param.set_param('muk_dms.forbidden_extensions', self.documents_forbidden_extensions)
        return res

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(
            documents_binary_max_size=int(params.get_param('muk_web_utils.binary_max_size', default=25)),
            documents_forbidden_extensions=params.get_param('muk_dms.forbidden_extensions', default=""),
        )
        return res
