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
import json
import urllib
import mimetypes
import logging

from openerp import _
from openerp import models, api, fields
from openerp.exceptions import ValidationError, AccessError

from . import muk_dms_base as base
from . import muk_dms_data as data
from . import muk_dms_root as root

_logger = logging.getLogger(__name__)

class File(base.DMSModel):
    _name = 'muk_dms.file'
    _description = "File"
    
    _inherit = ['mail.thread']
    
    #----------------------------------------------------------
    # Database
    #----------------------------------------------------------
    
    directory = fields.Many2one('muk_dms.directory', string="Directory", required=True)

    file_ref = fields.Reference(selection='_get_file_types', string="File Reference", readonly=True)
    
    filename = fields.Char(string='Filename', required=True)
    file = fields.Binary(string='File', store=False, required=True)
    
    file_extension = fields.Char(string='Extension', readonly=True)
    mime_type = fields.Char(string='Type', readonly=True)
    file_size = fields.Integer(string='Size', readonly=True)
    
    name = fields.Char(compute='_compute_name', string="Name")
    
    type = fields.Char(compute='_compute_type', string="File Type")
    
    link_download = fields.Char(compute='_compute_link_download', string="Download Link")
    link_preview = fields.Char(compute='_compute_link_preview', string="Preview Link")
    link_checkout = fields.Char(compute='_compute_link_checkout', string="Checkout Link")
    link_update = fields.Char(compute='_compute_link_update', string="Update Link")
    
    path_text = fields.Char(compute='_compute_path_text', string="Path")
    path_object = fields.Char(compute='_compute_path_object', string="Path")
    
    is_locked_flag = fields.Boolean(compute='_compute_is_locked', string="Locked")
    is_editor = fields.Boolean(compute='_compute_is_editor', string="Editor")
    
    perm_create = fields.Boolean(compute='_compute_perm_create', string="Create")
    perm_read = fields.Boolean(compute='_compute_perm_read', string="Read")
    perm_write = fields.Boolean(compute='_compute_perm_write', string="Write")
    perm_unlink = fields.Boolean(compute='_compute_perm_unlink', string="Delete")
    
    #----------------------------------------------------------
    # Local
    #----------------------------------------------------------
    
    file_types = [('muk_dms.data', _('Data'))]
    
    #----------------------------------------------------------
    # Functions
    #----------------------------------------------------------
    
    def get_path(self, include_self=True):
        path = include_self and str(self.filename) + "/" or ""
        if self.directory.check_existence():
            path = self.directory.get_path() + path
        return path
    
    def get_file_data(self):
        return self._get_file()
    
    def _get_file(self):
        return self.file_ref and self.file_ref.sudo().data() or None
    
    def _create_file(self, values, rec_dir, rec_root):
        if rec_root.save_type == root.SAVE_DATABASE:
            return self.env['muk_dms.database_data'].sudo().create({'file': values['file']})
        return False
    
    def _update_file(self, command, values):
        if self.file_ref and self.file_ref.id:
            self.file_ref.sudo().update(command, values)

    def _delete_file(self):
        if self.file_ref and self.file_ref.id:
            ref = self.file_ref
            self.file_ref = None
            ref.sudo().delete()
            ref.sudo().unlink()
        return True
    
    #----------------------------------------------------------
    # Selections
    #----------------------------------------------------------
    
    def _get_file_types(self):
        return self.file_types
    
    #----------------------------------------------------------
    # Locking
    #----------------------------------------------------------

    @api.multi
    def check_lock(self):
        self.ensure_one()
        lock = self.is_locked()
        if lock:
            return [lock.id, lock.locked_by_ref.id or "system"]
        else:
            return False
        
    @api.one
    def user_lock(self):
        lock = self.is_locked()
        if lock:
            raise AccessError(_("File is already locked."))
        return self.lock(self.env.user)
    
    @api.one
    def user_unlock(self):
        lock = self.is_locked()
        if lock:
            if lock and lock.locked_by_ref and lock.locked_by_ref.id == self.env.user.id:
                self.unlock()
            else:
                raise AccessError(_("No rights to unlock the file."))
    
    #----------------------------------------------------------
    # Read, View 
    #----------------------------------------------------------

    @api.one
    @api.depends('filename')
    def _compute_name(self):
        self.name = self.filename and os.path.splitext(self.filename)[0] or ""
    
    @api.one
    @api.depends('file_ref')
    def _compute_type(self):
        self.type = self.file_ref and self.file_ref.get_type() or _("No Data")
    
    @api.one
    def _compute_link_download(self):
        self.link_download = "/dms/file/download/" + str(self.id)
    
    @api.one
    def _compute_link_preview(self):
        self.link_preview = "/dms/file/preview?id=" + str(self.id)
    
    
    @api.one
    def _compute_link_checkout(self):
        self.link_checkout = "/dms/file/checkout/" + str(self.id)
        
    @api.one
    def _compute_link_update(self):
        self.link_update = "/dms/file/update/" + str(self.id)
    
    @api.one
    @api.depends('filename', 'directory')
    def _compute_path_text(self):
        self.path_text = self.get_path(False)
    
    @api.one
    @api.depends('filename', 'directory')
    def _compute_path_object(self):
        path = []
        try:
            path.append({'id': int(self.id), 'name': self.filename or "New", 'model':self._name})
        except TypeError:
            # NewId can't be cast to integer
            path.append({'id':-1, 'name': self.filename or "New"})
        if self.directory.check_existence():
            for i, dir in enumerate(self.directory.get_parent_list()):
                try:
                    path.append({'id': int(dir.id), 'name': dir.name or "New", 'model':'muk_dms.directory'})
                except TypeError:
                    # NewId can't be cast to integer
                    path.append({'id': -1, 'name': dir.name or "New", 'model':'muk_dms.directory'})
        self.path_object = json.dumps(path[::-1])
    
    @api.one
    def _compute_is_locked(self):
        self.is_locked_flag = self.is_locked()
    
    @api.one
    def _compute_is_editor(self):
        self.is_editor = self.is_locked_by() == self.env.user
    
    @api.one
    def _compute_perm_create(self):
        self.perm_create = self.check_access_rights('create', raise_exception=False) and self.check_access_rule(operation='write') == None
    
    @api.one
    def _compute_perm_read(self):
        self.perm_read = self.check_access_rights('read', raise_exception=False) and self.check_access_rule(operation='read') == None
    
    @api.one
    def _compute_perm_write(self):
        self.perm_write = self.check_access_rights('write', raise_exception=False) and self.check_access_rule(operation='write') == None
    
    @api.one
    def _compute_perm_unlink(self):
        self.perm_unlink = self.check_access_rights('unlink', raise_exception=False) and self.check_access_rule(operation='unlink') == None
    
    def _append_field_values(self, index, result):
        result = super(File, self)._append_field_values(index, result)
        result[index]['file'] = "0 KB"
        return result
    
    #----------------------------------------------------------
    # Create, Update
    #----------------------------------------------------------
    
    @api.one
    @api.constrains('directory', 'filename')
    def _check_name(self):
        _logger.debug("Checking if the given filename isn't already taken...")
        if self.directory.check_existence():
            for rec in self.directory.files:
                if rec.filename == self.filename and rec != self:
                    raise ValidationError(_("Files on the same level have to have a unique filename."))
    
    @api.one
    @api.constrains('directory')
    def _check_root(self):
        _logger.debug("Checking if a root exists...")
        if not self.directory.get_root().check_existence():
            raise ValidationError(_("The file structure needs to have a root node to create files."))
    
    def _validate_values(self, values):
        super(File, self)._validate_values(values)
        _logger.debug("Checking the filename attribute...")
        if 'filename' in values:
          if not set(base.VALID_NAME_CHARS).issuperset(values['filename']):
              raise ValidationError(_("Some characters in the filename attribute are invalid."))
           
    def _append_values_create(self, values):
        values = super(File, self)._append_values_create(values)
        rec_dir = self.env['muk_dms.directory'].sudo().browse([values['directory']])
        rec_root = rec_dir.get_root()
        
        if not rec_root.check_existence():
            raise ValidationError(_("The file structure needs to have a root node to create files."))
        
        rec_file = self._create_file(values, rec_dir, rec_root)
        values['file_ref'] = rec_file._name + ',' + str(rec_file.id)
        
        values = self._set_filename_values(values, values['filename'])
        values = self._set_file_size(values, values['file'])
        return values

    def _onchange_values(self, values):
        self.lock()
        
    def _append_values_wirte(self, values):
        values = super(File, self)._append_values_wirte(values)
        if 'filename' in values:
            values = self._set_filename_values(values, values['filename'])
            self._update_file(data.RENAME, {'filename': values['filename']})
        if 'file' in values:
            values = self._set_file_size(values, values['file'])
            self._update_file(data.REPLACE, {'file': values['file']})
        return values
    
    def _follow_operation(self, values):
        self.unlock()
    
    def _set_filename_values(self, values, filename):
        type, encoding = mimetypes.guess_type(urllib.pathname2url(filename))
        values['mime_type'] = type or 'application/octet-stream'
        file_name, file_extension = os.path.splitext(filename)
        values['file_extension'] = file_extension
        return values
    
    def _set_file_size(self, values, file):
        decode_file = base64.b64decode(file)
        values['file_size'] = len(decode_file)
        return values

    @api.returns('self', lambda value: value.id)
    def copy(self, cr, uid, id, default=None, context=None):
        if context is None:
            context = {}
        context = context.copy()
        data = self.copy_data(cr, uid, id, default, context)
        record = self.browse(cr, uid, id, context)
        data['filename'] = _("Copy of ") + str(data['filename'])
        data['file'] = record._get_file()
        new_id = self.create(cr, uid, data, context)
        self.copy_translations(cr, uid, id, new_id, context)
        return new_id

    #----------------------------------------------------------
    # Delete
    #----------------------------------------------------------

    def prepare_unlink(self):
        _logger.debug("Unlinking reference file...")
        self._delete_file() 