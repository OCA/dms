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

from odoo import models, api, fields, tools
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

_img_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static/src/img'))

class Directory(models.Model):
    
    _name = 'muk_dms.directory'
    _description = "MuK Documents Directory"
    _inherit = [
        'muk_dms.locking',
        'muk_dms.access',
        'mail.thread',
        'mail.activity.mixin']

    _parent_store = True
    _parent_name = "parent_directory"
    _parent_order = 'parent_left'
    _order = 'parent_left'

    #----------------------------------------------------------
    # Database
    #----------------------------------------------------------
    
    name = fields.Char(
        string="Name", 
        required=True,
        index=True)
   
    is_root_directory = fields.Boolean(
        string="Root Directory", 
        default=False,
        help="""Indicates if the directory is a root directory. A root directory has a settings object,
            while a directory with a set parent inherits the settings form its parent.""")
    
    is_top_directory = fields.Boolean(
        string="Top Directory", 
        compute='_compute_is_top_directory',
        search='_search_is_top_directory')
   
    settings = fields.Many2one(
        comodel_name='muk_dms.settings', 
        string="Settings",
        store=True, 
        auto_join=True,
        ondelete='restrict',
        compute='_compute_settings')
    
    show_tree = fields.Boolean(
        string="Show Structure", 
        related="settings.show_tree",
        readonly=True)
    
    color = fields.Integer(
        string="Color")
    
    tags = fields.Many2many(
        comodel_name='muk_dms.tag',
        relation='muk_dms_directory_tag_rel', 
        column1='did',
        column2='tid',
        string='Tags')
    
    category = fields.Many2one(
        comodel_name='muk_dms.category', 
        string="Category")
    
    parent_directory = fields.Many2one(
        comodel_name='muk_dms.directory', 
        string="Parent Directory",
        domain="[('permission_create', '=', True)]",
        ondelete='restrict', 
        auto_join=True,
        index=True)
    
    child_directories = fields.One2many(
        comodel_name='muk_dms.directory', 
        inverse_name='parent_directory',
        copy=False,
        string="Subdirectories")
    
    parent_left = fields.Integer(
        string='Left Parent', 
        index=True)
    
    parent_right = fields.Integer(
        string='Right Parent',  
        index=True)
    
    files = fields.One2many(
        comodel_name='muk_dms.file', 
        inverse_name='directory',
        copy=False,
        string="Files")
        
    path = fields.Char(
        string="Path",
        index=True,
        store=True,
        readonly=True,
        compute='_compute_path')
    
    relational_path = fields.Text(
        string="Path",
        store=True,
        readonly=True,
        compute='_compute_relational_path')
    
    user_stars = fields.Many2many(
        comodel_name='res.users',
        relation='muk_dms_directory_star_rel',
        column1='did',
        column2='uid',
        string='Stars')
    
    starred = fields.Boolean(
        compute='_compute_starred',
        inverse='_inverse_starred',
        search='_search_starred',
        string="Starred")
    
    count_directories = fields.Integer(
        compute='_compute_count_directories',
        store=True,
        string="Subdirectories")
    
    count_files = fields.Integer(
        compute='_compute_count_files',
        store=True,
        string="Files")
    
    count_total_directories = fields.Integer(
        compute='_compute_count_elements',
        string="Total Subdirectories")
    
    count_total_files = fields.Integer(
        compute='_compute_count_elements',
        string="Total Files")
    
    size = fields.Integer(
        compute='_compute_count_elements',
        string="Size")    
    
    custom_thumbnail = fields.Binary(
        string="Custom Thumbnail")
    
    custom_thumbnail_medium = fields.Binary(
        string="Medium Custom Thumbnail")
    
    custom_thumbnail_small = fields.Binary(
        string="Small Custom Thumbnail")
    
    thumbnail = fields.Binary(
        compute='_compute_thumbnail',
        string="Thumbnail")

    thumbnail_medium = fields.Binary(
        compute='_compute_thumbnail_medium',
        string="Medium Thumbnail")
    
    thumbnail_small = fields.Binary(
        compute='_compute_thumbnail_small',
        string="Small Thumbnail")
        
    #----------------------------------------------------------
    # Functions
    #----------------------------------------------------------
    
    @api.multi
    def lock_tree(self, user=None, refresh=False, operation=None, lock_self=True):
        if lock_self:
            self.lock(operation=operation, refresh=refresh)
        for record in self:
            record.child_directories.lock_tree(operation=operation, refresh=refresh)
            record.files.lock(operation=operation, refresh=refresh)
    
    @api.multi      
    def unlock_tree(self, refresh=False):
        self.unlock(refresh=refresh)
        for record in self:
            record.child_directories.unlock_tree(refresh=refresh)
            record.files.unlock(refresh=refresh)
            
    @api.multi
    def notify_change(self, values, *largs, **kwargs):
        super(Directory, self).notify_change(values, *largs, **kwargs)
        for record in self:
            record.child_directories.notify_change(values)
            record.files.notify_change(values)
    
    @api.multi  
    def trigger_computation_up(self, fields, *largs, **kwargs):
        if("no_trigger_computation_up" not in self.env.context):
            self.mapped('parent_directory').suspend_security().with_context(is_parent=True).trigger_computation(fields)
    
    @api.multi
    def trigger_computation_down(self, fields, *largs, **kwargs):
        if("no_trigger_computation_down" not in self.env.context):
            self.mapped('child_directories').suspend_security().with_context(is_child=True).trigger_computation(fields)
            self.mapped('files').suspend_security().trigger_computation(fields) 

    @api.multi
    def trigger_computation(self, fields, *largs, **kwargs):        
        super(Directory, self).trigger_computation(fields, refresh=True, *largs, **kwargs)
        for record in self:
            values = {}
            if "settings" in fields and not record.is_root_directory:
                values.update(record._compute_settings(write=False))
            if "path" in fields:
                values.update(record._compute_path(write=False))
                values.update(record._compute_relational_path(write=False))
            if values:
                record.write(values)
            if "settings" in fields or "path" in fields:
                record.trigger_computation_down(fields)
    
    #----------------------------------------------------------
    # Search
    #----------------------------------------------------------
    
    @api.model
    def _search_is_top_directory(self, operator, operand):
        directories = self.search([]).filtered(
            lambda d: d.is_root_directory or
            not d.parent_directory.check_access('read'))
        if operator == '=' and operand:
            return [('id', 'in', directories.mapped('id'))]
        return [('id', 'not in', directories.mapped('id'))]
    
    @api.model
    def _search_starred(self, operator, operand):
        if operator == '=' and operand:
            return [('user_stars', 'in', [self.env.uid])]
        return [('user_stars', 'not in', [self.env.uid])]

    #----------------------------------------------------------
    # Read, View 
    #----------------------------------------------------------
    
    @api.multi
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
    
    @api.multi
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
        
    @api.multi  
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
    
    @api.multi
    def _compute_count_elements(self, write=True):
        def get_elements(record):
            output = [0, 0, 0]
            for directory in record.child_directories:
                result = list(directory._compute_count_elements(write=False).values())
                output[0] = output[0] + result[0]
                output[1] = output[1] + result[1]
                output[2] = output[2] + result[2]
            for file in record.files:
                output[0] = output[0] + file.size
            output[1] = output[1] + len(record.files)
            output[2] = output[2] + len(record.child_directories)
            return output
        if write:
            for record in self:
                result = get_elements(record)
                record.update({
                    'size': result[0],
                    'count_total_files': result[1],
                    'count_total_directories': result[2]})
        else:
            self.ensure_one()
            result = get_elements(self)
            return {
                'size': result[0],
                'count_total_files': result[1],
                'count_total_directories': result[2]}
    
    @api.multi
    def _compute_starred(self):
        for record in self:
            record.starred = self.env.user in record.user_stars
    
    @api.depends('is_root_directory', 'parent_directory')
    def _compute_is_top_directory(self):
        for record in self:
            root = record.is_root_directory
            access = record.parent_directory.check_access('read')
            record.is_top_directory = root or not access
    
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
    
    @api.depends('custom_thumbnail_medium')
    def _compute_thumbnail_medium(self):
        for record in self:
            if record.custom_thumbnail_medium:
                record.thumbnail_medium = record.with_context({}).custom_thumbnail_medium        
            else:
                with open(os.path.join(_img_path, "folder_128x128.png"), "rb") as image_file:
                    record.thumbnail_medium = base64.b64encode(image_file.read())
    
    @api.depends('custom_thumbnail_small')
    def _compute_thumbnail_small(self):
        for record in self:
            if record.custom_thumbnail_small:
                record.thumbnail_small = record.with_context({}).custom_thumbnail_small     
            else:
                with open(os.path.join(_img_path, "folder_64x64.png"), "rb") as image_file:
                    record.thumbnail_small = base64.b64encode(image_file.read())
             
    #----------------------------------------------------------
    # Create, Update, Delete
    #----------------------------------------------------------
    
    @api.onchange('is_root_directory') 
    def _onchange_directory_type(self):
        if self.is_root_directory:
            self.parent_directory = None
        else:
            self.settings = None
    
    @api.constrains('is_root_directory', 'settings', 'parent_directory')
    def _check_settings(self):
        for record in self:
            if record.is_root_directory and not record.settings:
                raise ValidationError("A root directory has to have a settings object.")
            if not record.is_root_directory and not record.parent_directory:
                raise ValidationError("A directory has to have a parent directory.")
        
    @api.constrains('name')
    def _check_name(self):
        for record in self:
            if not record.check_name(self.name):
                raise ValidationError("The directory name is invalid.")
            if record.is_root_directory:
                childs = record.sudo().settings.root_directories.mapped(lambda rec: [rec.id, rec.name])
            else:
                childs = record.sudo().parent_directory.child_directories.mapped(lambda rec: [rec.id, rec.name])
            duplicates = [rec for rec in childs if rec[1] == record.name and rec[0] != record.id]
            if duplicates:
                raise ValidationError("A directory with the same name already exists.")
    
    @api.constrains('parent_directory')
    def _check_directory_access(self):
        for record in self:
            record.parent_directory.check_access('create', raise_exception=True)
    
    @api.multi
    def _inverse_starred(self):
        starred_records = self.env['muk_dms.directory'].sudo()
        not_starred_records = self.env['muk_dms.directory'].sudo()
        for record in self:
            if self.env.user in record.user_stars:
                starred_records |= record
            else:
                not_starred_records |= record
        not_starred_records.write({
            'user_stars': [(4, self.env.uid)]})
        starred_records.write({
            'user_stars': [(3, self.env.uid)]})
    
    @api.model
    def _before_create(self, vals, *largs, **kwargs):
        tools.image_resize_images(
            vals, big_name='custom_thumbnail',
            medium_name='custom_thumbnail_medium',
            small_name='custom_thumbnail_small')
        return super(Directory, self)._before_create(vals, *largs, **kwargs)

    @api.multi
    def _before_write(self, vals, *largs, **kwargs):
        tools.image_resize_images(
            vals, big_name='custom_thumbnail',
            medium_name='custom_thumbnail_medium',
            small_name='custom_thumbnail_small')
        return super(Directory, self)._before_write(vals, *largs, **kwargs)
    
    @api.multi
    def _before_write_operation(self, vals, operation, *largs, **kwargs):
        vals = super(Directory, self)._before_write_operation(vals, operation, *largs, **kwargs)
        operation = self.env.context['operation'] if 'operation' in self.env.context else operation
        for record in self:
            if record.settings.system_locks and not 'operation' in self.env.context:
                record.lock_tree(operation=operation, refresh=True, lock_self=False)
        return vals

    @api.multi
    def _after_write_operation(self, result, vals, operation, *largs, **kwargs):
        result = super(Directory, self)._after_write_operation(result, vals, operation, *largs, **kwargs)
        if not 'operation' in self.env.context:
            self.unlock_operation(operation=operation, refresh=True)
        return result
            
    @api.multi
    def _before_unlink_operation(self, operation, *largs, **kwargs):
        super(Directory, self)._before_unlink_operation(operation, *largs, **kwargs)
        operation = self.env.context['operation'] if 'operation' in self.env.context else operation
        for record in self:
            if record.settings.system_locks and not 'operation' in self.env.context:
                record.lock_tree(operation=operation, refresh=True, lock_self=False)
            record.files.with_context(operation=operation).unlink()
            record.child_directories.with_context(operation=operation).unlink()
    
    @api.multi
    def _after_unlink_operation(self, result, operation, *largs, **kwargs):
        super(Directory, self)._after_unlink_operation(result, operation, *largs, **kwargs)
        if not 'operation' in self.env.context:
            self.unlock_operation(operation=operation, refresh=True)
    
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
    
    @api.multi
    def _check_recomputation(self, vals, olds, *largs, **kwargs):
        super(Directory, self)._check_recomputation(vals, olds, *largs, **kwargs)
        roots = self.filtered(lambda d: d.is_root_directory == True)
        dirs = self - roots
        roots_fields = []
        dirs_fields = []
        if 'name' in vals:
            roots_fields.extend(['path'])
            dirs_fields.extend(['path'])
        if 'settings' in vals:
            roots_fields.extend(['settings'])
        if 'parent_directory' in vals:
            dirs_fields.extend(['settings', 'path'])
        if roots_fields:
            roots.trigger_computation(roots_fields)
        if dirs_fields:
            dirs.trigger_computation(dirs_fields)