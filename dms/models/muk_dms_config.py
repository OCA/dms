# -*- coding: utf-8 -*-

###################################################################################
# 
#    MuK Document Management System
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

from odoo import models, fields

class DMSConfigSettings(models.TransientModel):
    _name = 'muk_dms.config.settings'
    _inherit = 'res.config.settings'

    module_muk_dms_file = fields.Boolean('File System Support',
        help='Save Documents to a local file system.\n'
        '- This installs the module muk_dms_file.'
    )
    
    module_muk_dms_attachment = fields.Boolean('Attachment Support',
        help='Adds support for Odoo attachments.\n'
        '- This installs the module muk_dms_attachment.'
    )
    
    module_muk_dms_finder = fields.Boolean('Document Finder',
        help='Provides a Web Finder to manage the Documents.\n'
        '- This installs the module muk_dms_finder.'
    )
    
    module_muk_dms_access = fields.Boolean('Access Rights',
        help='Adds additional access rights for Documents.\n'
        '- This installs the module muk_dms_access.'
    )
    
    module_muk_dms_search = fields.Boolean('Advanced Search',
        help='Adds a full-text search for Documents.\n'
        '- This installs the module muk_dms_search.'
    )