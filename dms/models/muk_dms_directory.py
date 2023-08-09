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

import json
import logging

from openerp import _
from openerp import models, api, fields
from openerp.osv import osv
from openerp.exceptions import ValidationError, AccessError

from . import muk_dms_base as base

_logger = logging.getLogger(__name__)

class Directory(base.DMSModel):
    _name = 'muk_dms.directory'
    _description = "Directory"
    
    _parent_store = True
    _parent_name = "parent_id"
    _parent_order = 'parent_left'
    _order = 'parent_left'

    _inherit = ['mail.thread']
    
    #----------------------------------------------------------
    # Database
    #----------------------------------------------------------
    
    name = fields.Char(string="Name", required=True)

    parent_id = fields.Many2one('muk_dms.directory', string="Parent", select=True,
                             help="Every directory has a parent accept the root.")
    child_id = fields.One2many('muk_dms.directory', 'parent_id', string="Subdirectories")
    parent_left = fields.Integer(string='Left Parent', select=1)
    parent_right = fields.Integer(string='Right Parent', select=1)
        
    files = fields.One2many('muk_dms.file', 'directory', string="Files")
    
    root = fields.Many2one('muk_dms.root', string="Root", store=False, readonly=True)
    
    path_text = fields.Char(compute='_compute_path_text', string="Path")
    path_object = fields.Char(compute='_compute_path_object', string="Path")
    is_root_directory = fields.Boolean(compute='_compute_is_root_directory', string="Root Directory")
    
    count_dirctories = fields.Char(compute='_compute_count_dirctories', string="Subdirectories")
    count_files = fields.Char(compute='_compute_count_files', string="Files")
    
    size = fields.Integer(compute='_compute_size', string="Size")
    
    perm_create = fields.Boolean(compute='_compute_perm_create', string="Create")
    perm_read = fields.Boolean(compute='_compute_perm_read', string="Read")
    perm_write = fields.Boolean(compute='_compute_perm_write', string="Write")
    perm_unlink = fields.Boolean(compute='_compute_perm_unlink', string="Delete")
    
    #----------------------------------------------------------
    # Functions
    #----------------------------------------------------------
    
    def is_root_direcotry(self):
        return (not self.parent_id.check_existence())
    
    def get_path(self):
        path = str(self.name) + "/"
        if not self.is_root_direcotry():
            path = self.parent_id.get_path() + path
        return path
    
    def get_parent_list(self):
        parents = [self]
        if not self.is_root_direcotry():
            parents.extend(self.parent_id.get_parent_list())
        return parents
    
    def get_size(self):
        size = 0
        for file in self.files:
            size += file.file_size
        for child in self.child_id:
            size += child.get_size()
        return size
    
    @api.returns('muk_dms.directory')
    def find_root_directory(self):
        if self.is_root_direcotry():
            return self 
        else:
            return self.parent_id.find_root_directory()
        
    @api.returns('muk_dms.root')
    def get_root(self):
        return self.env['muk_dms.root'].sudo().search([['root_directory', '=',
                                                            self.find_root_directory().id]], limit=1)
    
    def notify_change(self, change, values):
        super(Directory, self).notify_change(change, values)
        self.notify_change_subtree(change, values)
                
    def notify_change_subtree(self, change, values):
        for file in self.files:
             file.notify_change(change, values)
        for directory in self.child_id:
            directory.notify_change(change, values)
    
    #----------------------------------------------------------
    # Locking
    #----------------------------------------------------------
    
    def _checking_lock(self):
        super(Directory, self)._checking_lock()
        if self.check_lock():
             raise AccessError(_("The record is locked, so it can't be changes or deleted."))
            
    def check_lock(self):
        if self.is_locked():
            return True
        for file in self.files:
            if file.is_locked():
                return True
        for directory in self.child_id:
            if directory.check_lock():
                return True
        return False
    
    def lock_tree(self):
        self.lock()
        for file in self.files:
            file.lock()
        for directory in self.child_id:
            directory.lock_tree()
            
    def unlock_tree(self):
        self.unlock()
        for file in self.files:
            file.unlock()
        for directory in self.child_id:
            directory.unlock_tree()
                
    #----------------------------------------------------------
    # Read, View 
    #----------------------------------------------------------
    
    @api.one
    @api.depends('name', 'parent_id')
    def _compute_path_text(self):
        self.path_text = self.get_path()
    
    @api.one
    @api.depends('name', 'parent_id')
    def _compute_path_object(self):
        path = []
        for i, dir in enumerate(self.get_parent_list()):
            try:
                path.append({'id': int(dir.id), 'name': dir.name or "New", 'model':self._name})
            except TypeError:
                # NewId can't be cast to integer
                path.append({'id':-1, 'name': dir.name or "New", 'model':self._name})
        self.path_object = json.dumps(path[::-1])

    @api.one
    @api.depends('parent_id')
    def _compute_is_root_directory(self):
        self.is_root_directory = self.is_root_direcotry()

    @api.one
    @api.depends('child_id')
    def _compute_count_dirctories(self):
        self.count_dirctories = len(self.child_id)
     
    @api.one
    @api.depends('files')
    def _compute_count_files(self):
        self.count_files = len(self.files)
    
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
    
    @api.one
    @api.depends('child_id', 'files')
    def _compute_size(self):
        self.path_text = self.get_path()
    
    def _append_field_values(self, index, result):
        result = super(Directory, self)._append_field_values(index, result)
        result[index]['root'] = self.get_root().id
        return result

    #----------------------------------------------------------
    # Create, Update
    #----------------------------------------------------------
    
    @api.one
    @api.constrains('parent_id', 'name')
    def _check_name(self):
        _logger.debug("Checking if the given name isn't already taken...")
        if self.parent_id.check_existence():
            for rec in self.parent_id.child_id:
                if rec.name == self.name and rec != self:
                    raise ValidationError(_("Directories on the same level have to have a unique name."))
    
    @api.one
    @api.constrains('parent_id')
    def _check_parent(self):
        _logger.debug("Checking if the given parent doesn't refer to itself...")
        if self.parent_id.id == self.id:
            raise ValidationError(_("Directory can't be referring to itself as root."))

    def _validate_values(self, values):
        super(Directory, self)._validate_values(values)
        _logger.debug("Checking the name attribute...")
        if 'name' in values:
          if not set(base.VALID_NAME_CHARS).issuperset(values['name']):
              raise ValidationError(_("Some characters in the name attribute are invalid."))
          
    def _onchange_values(self, values):
        self.lock_tree()
        
    def _follow_operation(self, values):
        self.unlock_tree()
        
    @api.returns('self', lambda value: value.id)
    def copy(self, cr, uid, id, default=None, context=None):
        raise AccessError(_('It is not possible to duplicate a directory, please create a new one.'))
    
    #----------------------------------------------------------
    # Delete
    #----------------------------------------------------------

    def prepare_unlink(self):
        _logger.debug("Unlinking subtree...")
        for file in self.files:
            file.unlink()
        for directory in self.child_id:
            directory.unlink()
