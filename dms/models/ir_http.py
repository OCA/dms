###################################################################################
#
#    Copyright (C) 2018 MuK IT GmbH
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

import base64
import logging
import mimetypes

from odoo import models
from odoo.exceptions import AccessError
from odoo.http import request, STATIC_CACHE
from odoo.tools.mimetypes import guess_mimetype

_logger = logging.getLogger(__name__)

class IrHttp(models.AbstractModel):
    
    _inherit = 'ir.http'
    
    @classmethod
    def binary_content(cls, xmlid=None, model='ir.attachment', id=None, field='datas',
                       unique=False, filename=None, filename_field='datas_fname', download=False,
                       mimetype=None, default_mimetype='application/octet-stream',
                       access_token=None, env=None):
        res_status, res_headers, res_content = super(IrHttp, cls).binary_content(
            xmlid=xmlid, model=model, id=id, field=field, unique=unique, filename=filename,
            filename_field=filename_field, download=download, mimetype=mimetype,
            default_mimetype=default_mimetype, access_token=access_token, env=env)
        if model == "muk_dms.file" and field != 'content':
            headers = []
            env = env or request.env
            for header in res_headers:
                if header[0] == 'Content-Type':
                    if not mimetype:
                        if filename:
                            mimetype = mimetypes.guess_type(filename)[0]
                        if not mimetype and getattr(env[model]._fields[field], 'attachment', False):
                            attach_mimetype = env['ir.attachment'].search_read(
                                domain=[
                                    ('res_model', '=', model),
                                    ('res_id', '=', id),
                                    ('res_field', '=', field)],
                                fields=['mimetype'], limit=1)
                            mimetype = attach_mimetype and attach_mimetype[0]['mimetype']
                        if not mimetype:
                            mimetype = guess_mimetype(base64.b64decode(res_content), default=default_mimetype)
                    headers.append(('Content-Type', mimetype))
                else:
                    headers.append(header)
            return res_status, headers, res_content
        return res_status, res_headers, res_content
        