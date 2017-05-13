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

import os
import base64
import email
import urllib
import logging
import cStringIO
import mimetypes
import werkzeug.exceptions

from odoo import _
from odoo import tools
from odoo import http
from odoo.http import *

_logger = logging.getLogger(__name__)

try:
    import mammoth
except ImportError:
    _logger.warn('Can not `import mammoth`.')

class Main(http.Controller):
    
    @http.route('/dms/file/preview', auth="user", type='http')
    def preview(self, id, **kw):
        return self._get_file(request.env['muk_dms.file'].search([('id', '=', id)]))
    
    @http.route('/dms/parse/mail', auth="user", type='http')
    def parse_mail(self, id, **kw):
        file = request.env['muk_dms.file'].search([('id', '=', id)], limit=1)
        if file and file.mime_type == 'message/rfc822':
            return Response(json.dumps(self._parse_mail(email.message_from_string(base64.b64decode(file.get_file_data())), id)),
                            content_type='application/json;charset=utf-8', status=200)
        else:
            return werkzeug.exceptions.BadRequest() 
    
    @http.route('/dms/attachment/preview', auth="user", type='http')
    def preview_attachment(self, id, filename, **kw):
        file = request.env['muk_dms.file'].search([('id', '=', id)], limit=1)
        if file and file.mime_type == 'message/rfc822':
            return self._get_attachment(email.message_from_string(base64.b64decode(file.get_file_data())), filename)
        else:
            return request.not_found("No mail with the given ID could be found.")
    
    @http.route('/dms/parse/msword', auth="user", type='http')
    def parse_msword(self, id, **kw):
        file = request.env['muk_dms.file'].search([('id', '=', id)], limit=1)
        if file and file.file_extension == '.docx':
            return Response(json.dumps(self._parse_msword(file)), content_type='application/json;charset=utf-8', status=200)
        else:
            return werkzeug.exceptions.BadRequest() 
    
    def _parse_mail(self, message, id):
        msg_dict = {}
        msg_dict['subject'] = message.get('Subject')
        msg_dict['From'] = message.get('From')
        msg_dict['To'] = message.get_all('To')
        msg_dict['CC'] = message.get('CC')
        msg_dict['InReplyTo'] = message.get('In-Reply-To')
        msg_dict['Date'] = message.get('Date')
        msg_dict['body'], msg_dict['attachments'] = self._parse_payload(message, id)
        return msg_dict

    def _parse_payload(self, message, id):
        attachments = []
        body = u''
        if not message.is_multipart() or message.get('content-type', '').startswith("text/"):
            body = tools.ustr(message.get_payload(), message.get_content_charset(), errors='replace')
            if message.get_content_type() == 'text/plain':
                body = tools.append_content_to_html(u'', body, preserve=True)      
        else:
            alternative = False
            mixed = False
            html = u''
            for part in message.walk():
                if part.get_content_type() == 'multipart/alternative':
                    alternative = True
                if part.get_content_type() == 'multipart/mixed':
                    mixed = True
                if part.get_content_maintype() == 'multipart':
                    continue
                
                filename = part.get_param('filename', None, 'content-disposition')
                if not filename:
                    filename = part.get_param('name', None)
                if filename:
                    if isinstance(filename, tuple):
                        filename = email.utils.collapse_rfc2231_value(filename).strip()
                    else:
                        filename = filename
                if filename: 
                    type, encoding = mimetypes.guess_type(urllib.pathname2url(filename))
                    file_name, file_extension = os.path.splitext(filename)
                    
                if filename or part.get('content-disposition', '').strip().startswith('attachment'):
                    attachments.append({'filename': filename or 'attachment',
                                        'url': "/dms/attachment/preview?id={}&filename={}".format(id, filename),
                                        'cid': part.get('Content-ID'),
                                        'ctype': part.get_content_type(),
                                        'encoding': encoding,
                                        'file_extension': file_extension})
                    continue
                
                if part.get_content_type() == 'text/plain' and (not alternative or not body):
                    body = tools.append_content_to_html(body, 
                                                        tools.ustr(part.get_payload(decode=True),
                                                                   part.get_content_charset(),
                                                                   errors='replace'),
                                                        preserve=True)
                elif part.get_content_type() == 'text/html':
                    append_content = not alternative or (html and mixed)
                    html = tools.ustr(part.get_payload(decode=True),
                                      part.get_content_charset(), errors='replace')
                    if not append_content:
                        body = html
                    else:
                        body = tools.append_content_to_html(body, html, plaintext=False)
                else:
                    attachments.append({'filename': filename or 'attachment',
                                        'url': "/dms/attachment/preview?id={}&filename={}".format(id, filename),
                                        'cid': part.get('Content-ID'),
                                        'ctype': part.get_content_type(),
                                        'encoding': encoding,
                                        'file_extension': file_extension})
        return body, attachments

    def _get_attachment(self, message, search_filename):
        if  message.is_multipart():
            for part in message.walk():
                filename = part.get_param('filename', None, 'content-disposition')
                if filename:
                    if isinstance(filename, tuple):
                        filename = email.utils.collapse_rfc2231_value(filename).strip()
                    if filename == search_filename:    
                        type, encoding = mimetypes.guess_type(urllib.pathname2url(filename))
                        file_name, file_extension = os.path.splitext(filename)
                        return self._make_file_response(part.get_payload(), filename, type)
        return request.not_found("No attachment with the given filename could be found.")    
    
    def _parse_msword(self, file):
        result = mammoth.convert_to_html(cStringIO.StringIO(base64.b64decode(file.get_file_data())))
        return {'result': result.value, 'message': result.messages}
        
    @route('/dms/file/download/<int:id>', auth='user', type="http")
    def download_file(self, id, **kw):
        return self._get_file(request.env['muk_dms.file'].search([('id', '=', id)]))
    
    @route('/dms/file/checkout/<int:id>', auth='user', type="http")
    def checkout_file(self, id, **kw):
        file = request.env['muk_dms.file'].search([('id', '=', id)], limit=1)
        if not file.is_locked():
            return self._get_file(file, checkout=True)
        else:
            return werkzeug.exceptions.Forbidden(_("File is already locked."))
    
    def _get_file(self, record, checkout=False):
        if len(record) != 1:
            response = request.not_found("No file with the given ID could be found.")
        elif not record.file_ref:
            response = request.not_found("The file object has no data.")
        else:
            if checkout:
                response = self._make_file_response(record.get_file_data(), record.filename, record.mime_type,
                                                    [('File-ID', str(record.id)), ('File-Token', record.user_lock()[0][0]['token'])])
            else:
                response = self._make_file_response(record.get_file_data(), record.filename, record.mime_type)
        return response
    
    def _make_file_response(self, file, filename, mimetype, additional_headers=[]):
        content = base64.b64decode(file)
        headers = [('Content-Type', mimetype),
                   ('Content-Disposition', 'attachment; filename={};'.format(filename)),
                   ('Content-Length', len(content))]
        headers.extend(additional_headers)
        return request.make_response(content, headers)
    
    @http.route('/dms/file/update', auth="user", type='http', methods=['GET'])
    def update(self, **kw):
        return request.render('muk_dms.muk_dms_template_update_form')
    
    @http.route('/dms/file/update', auth="user", type='http', methods=['POST'], csrf=False)
    def upload(self, filename, file_base64, token, **kw):
        lock = request.env['muk_dms.lock'].sudo().search([('token', '=', token)], limit=1)
        if not lock.id or lock.locked_by_ref != request.env.user or lock.token != token:
             return werkzeug.exceptions.Forbidden()
        file = lock.lock_ref
        file.user_unlock()
        file.write({'filename': filename, 'file': file_base64})
        return request.render('muk_dms.muk_dms_template_update_form')
    
    @http.route('/dms/query/directories', auth="user", type='http')
    def directories(self, query=False, **kw):
        val = []
        directories = query and request.env['muk_dms.directory'].search([('name', 'ilike', query)]) or request.env['muk_dms.directory'].search([])
        for directory in directories:
            val.append({'directory_id': directory.id, 'directory_name': directory.name})
        return Response(json.dumps(val), content_type='application/json;charset=utf-8', status=200) 
           