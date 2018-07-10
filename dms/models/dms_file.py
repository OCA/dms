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
import mimetypes
import itertools

from odoo import _
from odoo import models, api, fields, tools
from odoo.tools.mimetypes import guess_mimetype
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

_img_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static/src/img'))

class File(models.Model):
    
    _name = 'muk_dms.file'
    _description = "File"
    _inherit = [
        'muk_dms.locking',
        'muk_dms.access',
        'mail.thread',
        'mail.activity.mixin']
    
    #----------------------------------------------------------
    # Database
    #----------------------------------------------------------
    
    name = fields.Char(
        string="Filename", 
        required=True,
        index=True)
    
    active = fields.Boolean(
        string="Archived", 
        default=True,
        help="If a file is set to archived, it is not displayed, but still exists.")
    
    is_top_file = fields.Boolean(
        string="Top Directory", 
        compute='_compute_is_top_file',
        search='_search_is_top_file')
    
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
        relation='muk_dms_file_tag_rel', 
        column1='fid',
        column2='tid',
        string='Tags')
    
    category = fields.Many2one(
        string="Category",
        comodel_name='muk_dms.category', 
        related="directory.category",
        readonly=True,
        store=True)
    
    content = fields.Binary(
        string='Content', 
        required=True,
        compute='_compute_content',
        inverse='_inverse_content')
    
    reference = fields.Reference(
        selection=[('muk_dms.data', _('Data'))],
        string="Data Reference", 
        readonly=True)
    
    directory = fields.Many2one(
        comodel_name='muk_dms.directory', 
        string="Directory",
        domain="[('permission_create', '=', True)]",
        ondelete='restrict',  
        auto_join=True,
        required=True)
    
    extension = fields.Char(
        string='Extension',
        compute='_compute_extension',
        readonly=True,
        store=True)
    
    mimetype = fields.Char(
        string='Type',
        compute='_compute_mimetype',
        readonly=True,
        store=True)
    
    size = fields.Integer(
        string='Size', 
        readonly=True)
    
    path = fields.Char(
        string="Path",
        store=True,
        index=True,
        readonly=True,
        compute='_compute_path')
    
    relational_path = fields.Text(
        string="Path",
        store=True,
        readonly=True,
        compute='_compute_relational_path')
    
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
    def notify_change(self, values, *largs, **kwargs):
        super(File, self).notify_change(values, *largs, **kwargs)
        if "save_type" in values:
            self._update_reference_type()
            
    @api.multi  
    def trigger_computation_up(self, fields, *largs, **kwargs):
        if("no_trigger_computation_up" not in self.env.context):
            self.mapped('directory').suspend_security().with_context(is_parent=True).trigger_computation(fields)
        
    @api.multi
    def trigger_computation(self, fields, *largs, **kwargs):        
        super(File, self).trigger_computation(fields, refresh=True, *largs, **kwargs)
        for record in self:
            values = {}
            if "settings" in fields:
                values.update(record._compute_settings(write=False)) 
            if "path" in fields:
                values.update(record._compute_path(write=False)) 
                values.update(record._compute_relational_path(write=False)) 
            if "extension" in fields:
                values.update(record._compute_extension(write=False)) 
            if "mimetype" in fields:
                values.update(record._compute_mimetype(write=False)) 
            if values:
                record.write(values)    
                if "settings" in fields:
                    record.notify_change({'save_type': record.settings.save_type})
    
    @api.model
    def max_upload_size(self):
        params = self.env['ir.config_parameter'].sudo()
        return int(params.get_param('muk_dms.max_upload_size', default=25))
    
    @api.model
    def forbidden_extensions(self):
        params = self.env['ir.config_parameter'].sudo()
        forbidden_extensions = params.get_param('muk_dms.forbidden_extensions', default="")
        return [x.strip() for x in forbidden_extensions.split(',')]
    
    #----------------------------------------------------------
    # Search
    #----------------------------------------------------------
    
    @api.model
    def _search_permission_create(self, operator, operand):
        res = super(File, self)._search_permission_create(operator, operand)
        records = self.browse(res[0][2]).filtered(lambda r: r.directory.check_access('create'))
        if operator == '=' and operand:
            return [('id', 'in', records.mapped('id'))]
        return [('id', 'not in', records.mapped('id'))]
    
    @api.model
    def _search_is_top_file(self, operator, operand):
        files = self.search([]).filtered(lambda f: not f.directory.check_access('read'))
        if operator == '=' and operand:
            return [('id', 'in', files.mapped('id'))]
        return [('id', 'not in', files.mapped('id'))]
    
    #----------------------------------------------------------
    # Read, View 
    #----------------------------------------------------------
        
    @api.multi
    def _compute_settings(self, write=True):
        if write:
            for record in self:
                record.settings = record.directory.settings   
        else:
            self.ensure_one()
            return {'settings': self.directory.settings.id}         
    
    @api.multi    
    def _compute_extension(self, write=True):
        if write:
            for record in self:
                record.extension = os.path.splitext(record.name)[1]
        else:
            self.ensure_one()
            return {'extension': os.path.splitext(self.name)[1]}
    
    @api.multi            
    def _compute_mimetype(self, write=True):
        def get_mimetype(record):
            mimetype = mimetypes.guess_type(record.name)[0]
            if (not mimetype or mimetype == 'application/octet-stream') and record.content:
                mimetype = guess_mimetype(base64.b64decode(record.content))
            return mimetype or 'application/octet-stream'
        if write:
            for record in self:
                record.mimetype = get_mimetype(record)
        else:
            self.ensure_one()
            return {'mimetype': get_mimetype(self)}   
    
    @api.multi      
    def _compute_path(self, write=True):
        if write:
            for record in self:
                record.path = "%s%s" % (record.directory.path, record.name)   
        else:
            self.ensure_one()
            return {'path': "%s%s" % (self.directory.path, self.name)}   
    
    @api.multi
    def _compute_relational_path(self, write=True):
        def get_relational_path(record):
            path = json.loads(record.directory.relational_path)
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
    def _compute_content(self):
        for record in self:
            record.content = record._get_content()
    
    @api.multi
    def _compute_permissions(self):
        super(File, self)._compute_permissions()
        for record in self:
            record.permission_create = record.permission_create and record.directory.check_access('create')

    @api.depends('directory')
    def _compute_is_top_file(self):
        for record in self:
            record.is_top_file = record.directory.check_access('read') 
            
    @api.depends('custom_thumbnail')
    def _compute_thumbnail(self):
        for record in self:
            if record.custom_thumbnail:
                record.thumbnail = record.with_context({}).custom_thumbnail        
            else:
                extension = record.extension and record.extension.strip(".") or ""
                path = os.path.join(_img_path, "file_%s.png" % extension)
                if not os.path.isfile(path):
                    path = os.path.join(_img_path, "file_unkown.png")
                with open(path, "rb") as image_file:
                    record.thumbnail = base64.b64encode(image_file.read())
                    
    @api.depends('custom_thumbnail_medium')
    def _compute_thumbnail_medium(self):
        for record in self:
            if record.custom_thumbnail_medium:
                record.thumbnail_medium = record.with_context({}).custom_thumbnail_medium        
            else:
                extension = record.extension and record.extension.strip(".") or ""
                path = os.path.join(_img_path, "file_%s_128x128.png" % extension)
                if not os.path.isfile(path):
                    path = os.path.join(_img_path, "file_unkown_128x128.png")
                with open(path, "rb") as image_file:
                    record.thumbnail_medium = base64.b64encode(image_file.read())
    
    @api.depends('custom_thumbnail_small')
    def _compute_thumbnail_small(self):
        for record in self:
            if record.custom_thumbnail_small:
                record.thumbnail_small = record.with_context({}).custom_thumbnail_small        
            else:
                extension = record.extension and record.extension.strip(".") or ""
                path = os.path.join(_img_path, "file_%s_64x64.png" % extension)
                if not os.path.isfile(path):
                    path = os.path.join(_img_path, "file_unkown_64x64.png")
                with open(path, "rb") as image_file:
                    record.thumbnail_small = base64.b64encode(image_file.read())
        
    #----------------------------------------------------------
    # Create, Update, Delete
    #----------------------------------------------------------
    
    @api.constrains('name')
    def _check_name(self):
        if not self.check_name(self.name):
            raise ValidationError(_("The file name is invalid."))
        childs = self.sudo().directory.files.mapped(lambda rec: [rec.id, rec.name])
        duplicates = [rec for rec in childs if rec[1] == self.name and rec[0] != self.id]
        if duplicates:
            raise ValidationError(_("A file with the same name already exists."))
        
    @api.constrains('name')
    def _check_extension(self):
        forbidden_extensions = self.forbidden_extensions()
        file_extension = self._compute_extension(write=False)['extension']
        if file_extension and file_extension in forbidden_extensions:
            raise ValidationError(_("The file has a forbidden file extension."))
        
    @api.constrains('content')
    def _check_size(self):
        max_upload_size = self.max_upload_size()
        if (max_upload_size * 1024 * 1024) < len(base64.b64decode(self.content)):
            raise ValidationError(_("The maximum upload size is %s MB).") % max_upload_size)
    
    @api.constrains('directory')
    def _check_directory_access(self):
        for record in self:
            record.directory.check_access('create', raise_exception=True)
    
    @api.multi
    def _inverse_content(self):
        for record in self:
            if record.content:
                content = record.content
                size = len(base64.b64decode(content))
                reference = record.reference
                if reference:
                    record._update_reference_values({'content': content})
                    record.write({'size': size})
                else:
                    directory = record.directory
                    settings = record.settings if record.settings else directory.settings
                    reference = record._create_reference(
                        settings, directory.path, record.name, content)
                    reference = "%s,%s" % (reference._name, reference.id)
                    record.write({'reference': reference, 'size': size})
            else:
                record._unlink_reference()
                record.reference = None
    
    @api.model
    def _before_create(self, vals, *largs, **kwargs):
        tools.image_resize_images(
            vals, big_name='custom_thumbnail',
            medium_name='custom_thumbnail_medium',
            small_name='custom_thumbnail_small')
        return super(File, self)._before_create(vals, *largs, **kwargs)

    @api.multi
    def _before_write(self, vals, *largs, **kwargs):
        tools.image_resize_images(
            vals, big_name='custom_thumbnail',
            medium_name='custom_thumbnail_medium',
            small_name='custom_thumbnail_small')
        return super(File, self)._before_write(vals, *largs, **kwargs)

    @api.multi
    def _before_unlink(self, *largs, **kwargs):
        info = super(File, self)._before_unlink(*largs, **kwargs)
        references = [
            list((k, list(map(lambda rec: rec.reference.id, v)))) 
               for k, v in itertools.groupby(
                   self.sorted(key=lambda rec: rec.reference._name),
                   lambda rec: rec.reference._name)]
        info['references'] = references
        return info
    
    @api.multi
    def _after_unlink(self, result, info, infos, *largs, **kwargs):
        super(File, self)._after_unlink(result, info, infos, *largs, **kwargs)
        if 'references' in info and info['references']:
            for tuple in info['references']:
                self.env[tuple[0]].sudo().browse(list(filter(None, tuple[1]))).unlink()
    
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or [])
        names = []
        if 'directory' in default:
            directory = self.env['muk_dms.directory'].sudo().browse(default['directory'])
            names = directory.files.mapped('name')
        else:
            names = self.sudo().directory.files.mapped('name')
        default.update({'name': self.unique_name(self.name, names, self.extension)})
        vals = self.copy_data(default)[0]
        if 'reference' in vals:
            del vals['reference']
        if not 'content' in vals:
            vals.update({'content': self.content})
        new = self.with_context(lang=None).create(vals)
        self.copy_translations(new)
        return new
    
    @api.multi
    def _check_recomputation(self, vals, olds, *largs, **kwargs):
        super(File, self)._check_recomputation(vals, olds, *largs, **kwargs)
        fields = []
        if 'name' in vals:
            fields.extend(['extension', 'mimetype', 'path'])
        if 'directory' in vals:
            fields.extend(['settings', 'path'])
        if 'content' in vals:
            fields.extend(['index_content'])
        if fields:
            self.trigger_computation(fields)
        self._check_reference_values(vals)
    
    #----------------------------------------------------------
    # Reference
    #----------------------------------------------------------
    
    @api.multi
    def _create_reference(self, settings, path, filename, content):
        self.ensure_one()
        self.check_access('create', raise_exception=True)
        if settings.save_type == 'database':
            return self.env['muk_dms.data_database'].sudo().create({'data': content})
        return None
    
    @api.multi
    def _update_reference_values(self, values):
        self.check_access('write', raise_exception=True)
        references = self.sudo().mapped('reference')
        if references:
            references.sudo().update(values)
    
    @api.multi
    def _update_reference_type(self):
        self.check_access('write', raise_exception=True)
        for record in self:
            if record.reference and record.settings.save_type != record.reference.type():
                reference = record._create_reference(
                    record.settings, record.directory.path, record.name, record.content)
                record._unlink_reference()
                record.reference = "%s,%s" % (reference._name, reference.id)
    
    @api.multi
    def _check_reference_values(self, values):
        self.check_access('write', raise_exception=True)
        if 'content' in values:
            self._update_reference_values({'content': values['content']})
        if 'settings' in values:
            self._update_reference_type()
            
    @api.multi
    def _get_content(self):
        self.ensure_one()
        self.check_access('read', raise_exception=True)
        return self.reference.sudo().content() if self.reference else None
    
    @api.multi
    def _unlink_reference(self):
        self.check_access('unlink', raise_exception=True)
        for tuple in [
            list((k, list(map(lambda rec: rec.reference.id, v)))) 
               for k, v in itertools.groupby(
                   self.sorted(key=lambda rec: rec.reference._name),
                   lambda rec: rec.reference._name)]:
            self.env[tuple[0]].sudo().browse(list(filter(None, tuple[1]))).unlink()