# -*- coding: utf-8 -*-

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

import os
import json
import base64
import logging

from odoo import _
from odoo import models, api, fields
from odoo.exceptions import ValidationError, AccessError

from odoo.addons.muk_dms.models import dms_base

_logger = logging.getLogger(__name__)

_img_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static/src/img'))

class Directory(dms_base.DMSModel):
    _name = 'muk_dms.directory'
    _description = "MuK Documents Directory"
    
    _inherit = 'muk_dms.access'

    _parent_store = True
    _parent_name = "parent_directory"
    _parent_order = 'parent_left'
    _order = 'parent_left'

    #----------------------------------------------------------
    # Database
    #----------------------------------------------------------
    
    name = fields.Char(
        string="Name", 
        required=True)
   
    is_root_directory = fields.Boolean(
        string="Root Directory", 
        default=False,
        help="Indicates if the directory is a root directory. A root directory has a settings object, " +
             "while a directory with a set parent inherits the settings form its parent.")
   
    settings = fields.Many2one(
        'muk_dms.settings', 
        string="Settings",
        store=True, 
        auto_join=True,
        ondelete='restrict',
        compute='_compute_settings')
    
    parent_directory = fields.Many2one(
        'muk_dms.directory', 
        string="Parent Directory",
        ondelete='restrict', 
        auto_join=True,
        index=True)
    
    child_directories = fields.One2many(
        'muk_dms.directory', 
        'parent_directory',
        copy=False,
        string="Subdirectories")
    
    parent_left = fields.Integer(
        string='Left Parent', 
        index=True)
    
    parent_right = fields.Integer(
        string='Right Parent', 
        index=True)
    
    files = fields.One2many(
        'muk_dms.file', 
        'directory',
        copy=False,
        string="Files")
    
    count_directories = fields.Integer(
        compute='_compute_count_directories',
        string="Subdirectories")
    
    count_files = fields.Integer(
        compute='_compute_count_files',
        string="Files")
    
    size = fields.Integer(
        compute='_compute_size',
        string="Size", 
        store=True)    
    
    custom_thumbnail = fields.Binary(
        string="Custom Thumbnail")
    
    thumbnail = fields.Binary(
        compute='_compute_thumbnail',
        string="Thumbnail")
        
    path = fields.Char(
        string="Path",
        store=True,
        compute='_compute_path')
    
    relational_path = fields.Text(
        string="Path",
        store=True,
        readonly=True,
        compute='_compute_relational_path')
        
    #----------------------------------------------------------
    # Functions
    #----------------------------------------------------------
    
    def lock_tree(self, user=None, refresh=False, operation=None, lock_self=True):
        if lock_self:
            self.lock(operation=operation)
        for record in self:
            record.child_directories.lock_tree(operation=operation)
            record.files.lock(operation=operation)
            
    def unlock_tree(self, refresh=False):
        self.unlock()
        for record in self:
            record.child_directories.unlock_tree()
            record.files.unlock()
    
    def notify_change(self, values, refresh=False, operation=None):
        super(Directory, self).notify_change(values, refresh)
        for child in self.child_directories:
            child.notify_change(values, refresh)
        for index, file in enumerate(self.files):
            if index == len(self.files) - 1:
                file.notify_change(values, refresh)
            else:
                file.notify_change(values, refresh)
        
    def trigger_computation_up(self, fields, operation=None):
        parent_directory = self.parent_directory
        if parent_directory:
            parent_directory.trigger_computation(fields, False)
            
    def trigger_computation_down(self, fields, operation=None):
        if self.settings.system_locks:
                self.lock_tree(operation=operation, lock_self=False)
        for child in self.child_directories:
            child.with_context(operation=operation, is_subnode=True).trigger_computation(fields, False, operation)
        for index, file in enumerate(self.files):
            if index == len(self.files) - 1:
                if self.env.context.get('is_subnode'):
                    file.with_context(operation=operation).trigger_computation(fields, False, operation) 
                else:
                    file.with_context(operation=operation).trigger_computation(fields, True, operation) 
            else:
                file.with_context(operation=operation).trigger_computation(fields, False, operation)
        self.unlock_tree()
            
    def trigger_computation(self, fields, refresh=True, operation=None):
        super(Directory, self).trigger_computation(fields, refresh, operation)
        values = {}
        if "settings" in fields:
            if not self.is_root_directory:
                values.update(self.with_context(operation=operation)._compute_settings(write=False))
        if "path" in fields:
            values.update(self.with_context(operation=operation)._compute_path(write=False))
            values.update(self.with_context(operation=operation)._compute_relational_path(write=False))
        if "size" in fields:
            values.update(self.with_context(operation=operation)._compute_size(write=False))
        if values:
            self.write(values);   
            if "settings" in fields or "path" in fields:
                self.trigger_computation_down(fields, operation)
            if "size" in fields:
                self.trigger_computation_up(fields, operation)
        
    #----------------------------------------------------------
    # Read, View 
    #----------------------------------------------------------
        
    def _compute_settings(self, write=True):
        if write:
            for record in self:
                if not record.is_root_directory:
                    record.settings = record.parent_directory.settings
        else:
            self.ensure_one()
            if self.is_root_directory:
                return {'settings': self.settings.id} 
            else:
                return {'settings': self.parent_directory.settings.id}        
    
    def _compute_path(self, write=True):
        def get_path(record):
            if record.is_root_directory:
                return "/%s/" % record.name
            else:
                return "%s%s/" % (record.parent_directory.path, record.name)
        if write:
            for record in self:
                record.path = get_path(record)
        else:
            self.ensure_one()
            return {'path': get_path(self)}        
                
    def _compute_relational_path(self, write=True):
        def get_relational_path(record):
            if record.is_root_directory:
                return json.dumps([{
                    'model': record._name,
                    'id': record.id,
                    'name': record.name}])
            else:
                path = json.loads(record.parent_directory.relational_path)
                path.append({
                    'model': record._name,
                    'id': record.id,
                    'name': record.name})
                return json.dumps(path)
        if write:
            for record in self:
                record.relational_path = get_relational_path(record)
        else:
            self.ensure_one()
            return {'relational_path': get_relational_path(self)}        
    
    def _compute_size(self, write=True):
        def get_size(record):
            size = 0
            for directory in record.child_directories:
                size += directory.size
            for file in record.files:
                size += file.size
            return size
        if write:
            for record in self:
                record.size = get_size(record)
        else:
            self.ensure_one()
            return {'size': get_size(self)}        
    
    @api.depends('child_directories')
    def _compute_count_directories(self):
        for record in self:
            record.count_directories = len(record.child_directories)
     
    @api.depends('files')
    def _compute_count_files(self):
        for record in self:
            record.count_files = len(record.files)
    
    @api.depends('custom_thumbnail')
    def _compute_thumbnail(self):
        for record in self:
            if record.custom_thumbnail:
                record.thumbnail = record.with_context({}).custom_thumbnail        
            else:
                with open(os.path.join(_img_path, "folder.png"), "rb") as image_file:
                    record.thumbnail = base64.b64encode(image_file.read())
             
    #----------------------------------------------------------
    # Create, Update, Delete
    #----------------------------------------------------------
    
    @api.onchange('is_root_directory') 
    def _onchange_directory_type(self):
        if self.is_root_directory:
           self.parent_directory = None
        else:
           self.settings = None
    
    def _before_create(self, vals):
        vals = super(Directory, self)._before_create(vals)
        is_root_directory = vals["is_root_directory"] if "is_root_directory" in vals else False
        if is_root_directory and not "settings" in vals:
            raise ValidationError("A root directory has to have a settings object.")
        if not is_root_directory and not "parent_directory" in vals:
            raise ValidationError("A directory has to have a parent directory.")
        return vals
    
    @api.constrains('settings', 'parent_directory')
    def _check_settings(self):
        if self.is_root_directory and not self.settings:
            raise ValidationError("A root directory has to have a settings object.")
        if not self.is_root_directory and not self.parent_directory:
            raise ValidationError("A directory has to have a parent directory.")
        
    @api.constrains('name')
    def _check_name(self):
        if not self.check_name(self.name):
            raise ValidationError("The directory name is invalid.")
        if self.is_root_directory:
            childs = self.sudo().settings.root_directories.mapped(lambda rec: [rec.id, rec.name])
        else:
            childs = self.sudo().parent_directory.child_directories.mapped(lambda rec: [rec.id, rec.name])
        duplicates = [rec for rec in childs if rec[1] == self.name and rec[0] != self.id]
        if duplicates:
            raise ValidationError("A directory with the same name already exists.")
    
    def _before_create(self, vals):
        if 'parent_directory' in vals and vals['parent_directory']:
            directory = self.browse(vals['parent_directory'])
            directory.check_access('create', raise_exception=True)
        return super(Directory, self)._before_create(vals)
    
    def _after_create(self, vals):
        record = super(Directory, self)._after_create(vals)
        record._check_recomputation(vals)
        return record
        
    def _after_write_record(self, vals, operation):
        vals = super(Directory, self)._after_write_record(vals, operation)
        self._check_recomputation(vals, operation)
        return vals
    
    def _check_recomputation(self, values, operation=None):
        fields = []
        if 'name' in values:
            fields.extend(['path'])
        if self.is_root_directory and 'settings' in values:
            fields.extend(['settings'])
        if not self.is_root_directory and 'parent_directory' in values:
            fields.extend(['settings', 'path'])
        if fields:
            self.trigger_computation(fields, operation=operation)
    
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or [])
        names = []
        if self.is_root_directory:
            names = self.sudo().settings.root_directories.mapped('name')
            default.update({'settings': self.settings.id})
        elif 'parent_directory' in default:
            parent_directory = self.env['muk_dms.directory'].sudo().browse(default['parent_directory'])
            names = parent_directory.child_directories.mapped('name')
        else:
            names = self.sudo().parent_directory.child_directories.mapped('name')
        default.update({'name': self.unique_name(self.name, names)})
        vals = self.copy_data(default)[0]
        new = self.with_context(lang=None).create(vals)
        self.copy_translations(new)
        for file in self.files:
            file.copy({'directory': new.id})
        for directory in self.child_directories:
            directory.copy({'parent_directory': new.id})
        return new
    
    def _before_unlink(self, operation):
        info = super(Directory, self)._before_unlink(operation)
        directories = set(record.parent_directory for record in self if record.parent_directory)
        info['directories'] = directories
        return info
            
    def _before_unlink_record(self, operation):
        info = super(Directory, self)._before_unlink_record(operation)
        operation = self.env.context['operation'] if 'operation' in self.env.context else operation
        if self.settings.system_locks and not 'operation' in self.env.context:
            info['lock_operation'] = operation
            self.lock_tree(operation=operation, lock_self=False)
        self.files.with_context(operation=operation).unlink()
        self.child_directories.with_context(operation=operation).unlink()
        return info
    
    def _after_unlink(self, result, info, infos, operation):
        super(Directory, self)._after_unlink(result, info, infos, operation)
        for info in infos:
            if 'lock_operation' in info:
                self.unlock_operation(info['lock_operation'], True)
            if 'directories' in info:
                for directory in info['directories']:
                    directory.trigger_computation(['size'])