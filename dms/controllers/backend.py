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

import logging

from odoo import _, http
from odoo.http import request

_logger = logging.getLogger(__name__)

class BackendController(http.Controller):
    
    @http.route('/config/muk_dms.max_upload_size', type='json', auth="user")
    def max_upload_size(self, **kw):
        params = request.env['ir.config_parameter'].sudo()
        return {
            'max_upload_size': int(params.get_param("muk_dms.max_upload_size", default=25))
        }

    @http.route('/config/muk_dms.forbidden_extensions', type='json', auth="user")
    def forbidden_extensions(self, **kw):
        params = request.env['ir.config_parameter'].sudo()
        return {
            'forbidden_extensions': params.get_param("muk_dms.forbidden_extensions", default="")
        }
    
    @http.route('/tree/create/directory', type='json', auth="user")
    def create_directory(self, parent_directory, name=None, context=None, **kw):
        parent = request.env['muk_dms.directory'].sudo().browse(parent_directory)
        uname = parent.unique_name(name or _("New Directory"), parent.child_directories.mapped('name'))
        directory = request.env['muk_dms.directory'].with_context(context or request.env.context).create({
            'name': uname,
            'parent_directory': parent_directory})
        return {
            'id': "directory_%s" % directory.id,
            'text': directory.name,
            'icon': "fa fa-folder-o",
            'type': "directory",
            'data': {
                'odoo_id': directory.id,
                'odoo_model': "muk_dms.directory",
                'odoo_record': False,
                'name': directory.name,
                'perm_read': directory.permission_read,
                'perm_create': directory.permission_create,
                'perm_write': directory.permission_write,
                'perm_unlink': directory.permission_unlink,
                'directories': directory.count_directories,
                'files': directory.count_files,
                'parent': "directory_%s" % parent_directory,
            },
            'children': False,
        }    