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

import os
import io
import json
import base64
import logging
import mimetypes
import itertools
import tempfile
import hashlib
import operator
import functools

from collections import defaultdict

from odoo import _, SUPERUSER_ID
from odoo import models, api, fields, tools
from odoo.tools.mimetypes import guess_mimetype
from odoo.exceptions import ValidationError
from odoo.exceptions import AccessError
from odoo.osv import expression

from odoo.addons.muk_utils.tools import file
from odoo.addons.muk_security.tools.security import NoSecurityUid

_logger = logging.getLogger(__name__)

class File(models.Model):
    
    _name = 'muk_dms.file'
    _description = "File"
    
    _inherit = [
        'muk_security.mixins.access_rights',
        'muk_security.mixins.locking',
        'muk_dms.mixins.thumbnail',
    ]
    
    _order = "name asc"
    
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
     
    directory = fields.Many2one(
        comodel_name='muk_dms.directory', 
        string="Directory",
        domain="[('permission_create', '=', True)]",
        context="{'dms_directory_show_path': True}",
        ondelete='restrict',  
        auto_join=True,
        required=True,
        index=True)
    
    storage = fields.Many2one(
        related="directory.storage",
        comodel_name='muk_dms.storage',
        string="Storage",
        auto_join=True,
        readonly=True,
        store=True)
    
    is_hidden = fields.Boolean(
        string="Storage is Hidden", 
        related="storage.is_hidden",
        readonly=True)

    company = fields.Many2one(
        related="storage.company",
        comodel_name='res.company',
        string='Company',
        readonly=True,
        store=True,
        index=True)
    
    path_names = fields.Char(
        compute='_compute_path',
        string="Path Names", 
        readonly=True,
        store=False)

    path_json = fields.Text(
        compute='_compute_path',
        string="Path Json", 
        readonly=True,
        store=False)
     
    color = fields.Integer(
        string="Color",
        default=0)
     
    category = fields.Many2one(
        comodel_name='muk_dms.category',
        context="{'dms_category_show_path': True}", 
        string="Category")
    
    tags = fields.Many2many(
        comodel_name='muk_dms.tag',
        relation='muk_dms_file_tag_rel',         
        column1='fid',
        column2='tid',
        string='Tags')
    
    content = fields.Binary(
        compute='_compute_content',
        inverse='_inverse_content',
        string='Content',
        attachment=False,
        prefetch=False, 
        required=True,
        store=False)
    
    extension = fields.Char(
        compute='_compute_extension',
        string='Extension',
        readonly=True,
        store=True)
     
    mimetype = fields.Char(
        compute='_compute_mimetype',
        string='Type',
        readonly=True,
        store=True)
    
    size = fields.Integer(
        string='Size',
        readonly=True)
    
    checksum = fields.Char(
        string="Checksum/SHA1",
        readonly=True, 
        size=40, 
        index=True)
    
    content_binary = fields.Binary(
        string="Content Binary",
        attachment=False,
        prefetch=False,
        invisible=True)
    
    save_type = fields.Char(
        compute='_compute_save_type',
        string='Current Save Type',
        invisible=True,
        prefetch=False)
    
    migration = fields.Char(
        compute='_compute_migration',
        string='Migration Status',
        readonly=True,
        prefetch=False)
    
    #----------------------------------------------------------
    # Helper
    #----------------------------------------------------------

    @api.model
    def _get_checksum(self, binary):
        return hashlib.sha1(binary or b'').hexdigest()
    
    @api.model
    def _get_content_inital_vals(self):
        return {'content_binary': False}
    
    @api.model
    def _update_content_vals(self, file, vals, binary):
        vals.update({
            'checksum': self._get_checksum(binary),
            'size': binary and len(binary) or 0,
        })
        return vals
    
    @api.model
    def _get_binary_max_size(self):
        get_param = self.env['ir.config_parameter'].sudo().get_param
        return int(get_param('muk_web_utils.binary_max_size', default=25))
     
    @api.model
    def _get_forbidden_extensions(self):
        get_param = self.env['ir.config_parameter'].sudo().get_param
        extensions = get_param('muk_dms.forbidden_extensions', default="")
        return [extension.strip() for extension in extensions.split(',')]

    @api.multi
    def _get_thumbnail_placeholder_name(self):
        return self.extension and "file_%s.svg" % self.extension or ""
    
    #----------------------------------------------------------
    # Actions
    #----------------------------------------------------------
    
    @api.multi
    def action_migrate(self, logging=True):
        record_count = len(self)
        for index, file in enumerate(self):
            if logging:
                info = (index + 1, record_count, file.migration)
                _logger.info(_("Migrate File %s of %s [ %s ]") % info)
            file.with_context(migration=True).write({
                'content': file.with_context({}).content
            })
    
    @api.multi
    def action_save_onboarding_file_step(self):
        self.env.user.company_id.set_onboarding_step_done(
            'documents_onboarding_file_state'
        )
    
    #----------------------------------------------------------
    # SearchPanel
    #----------------------------------------------------------  
    
    @api.model
    def _search_panel_directory(self, **kwargs):
        search_domain = kwargs.get('search_domain', []),
        category_domain = kwargs.get('category_domain', [])
        if category_domain and len(category_domain):
            return '=', category_domain[0][2]
        if search_domain and len(search_domain):
            for domain in search_domain[0]:
                if domain[0] == 'directory':
                    return domain[1], domain[2]
        return None, None
    
    @api.model
    def _search_panel_domain(self, field, operator, directory_id, comodel_domain=[]):
        files_ids = self.search([('directory', operator, directory_id)]).ids
        return expression.AND([comodel_domain, [(field, 'in', files_ids)]])
    
    @api.model
    def search_panel_select_range(self, field_name, **kwargs):
        operator, directory_id = self._search_panel_directory(**kwargs)
        if directory_id and field_name == 'directory':
            domain = [('parent_directory', operator, directory_id)]
            values = self.env['muk_dms.directory'].search_read(
                domain, ['display_name', 'parent_directory']
            )
            return {
                'parent_field': 'parent_directory',
                'values': values if len(values) > 1 else [],
            }
        return super(File, self).search_panel_select_range(field_name, **kwargs)
     
    @api.model
    def search_panel_select_multi_range(self, field_name, **kwargs):
        operator, directory_id = self._search_panel_directory(**kwargs)
        if field_name == 'tags':
            sql_query = '''
                SELECT t.name AS name, t.id AS id, c.name AS group_name,
                    c.id AS group_id, COUNT(r.fid) AS count
                FROM muk_dms_tag t
                JOIN muk_dms_category c ON t.category = c.id
                LEFT JOIN muk_dms_file_tag_rel r ON t.id = r.tid 
                {directory_where_clause}
                GROUP BY c.name, c.id, t.name, t.id
                ORDER BY c.name, c.id, t.name, t.id;
            '''
            where_clause = ''
            if directory_id:
                directory_where_clause = 'WHERE r.fid = ANY (VALUES {ids})'
                file_ids = self.search([('directory', operator, directory_id)]).ids
                where_clause = '' if not file_ids else directory_where_clause.format(
                    ids=', '.join(map(lambda id: '(%s)' % id, file_ids))
                )
            self.env.cr.execute(sql_query.format(directory_where_clause=where_clause), [])
            return self.env.cr.dictfetchall()
        if directory_id and field_name in ['directory', 'category']:
            comodel_domain = kwargs.pop('comodel_domain', [])
            directory_comodel_domain = self._search_panel_domain(
                'files', operator, directory_id, comodel_domain
            )
            return super(File, self).search_panel_select_multi_range(
                field_name, comodel_domain=directory_comodel_domain, **kwargs
            )
        return super(File, self).search_panel_select_multi_range(field_name, **kwargs)
    
    #----------------------------------------------------------
    # Read 
    #----------------------------------------------------------     
    
    @api.depends('name', 'directory', 'directory.parent_path')
    def _compute_path(self):
        records_with_directory = self - self.filtered(lambda rec: not rec.directory)
        if records_with_directory:
            paths = [list(map(int, rec.directory.parent_path.split('/')[:-1])) for rec in records_with_directory]
            model = self.env['muk_dms.directory'].with_context(dms_directory_show_path=False)
            directories = model.browse(set(functools.reduce(operator.concat, paths)))
            data = dict(directories._filter_access('read').name_get())
            for record in self:
                path_names = []
                path_json = []
                for id in reversed(list(map(int, record.directory.parent_path.split('/')[:-1]))):
                    if id not in data:
                        break
                    path_names.append(data[id])
                    path_json.append({
                        'model': model._name,
                        'name': data[id],
                        'id': id,
                    })
                path_names.reverse()
                path_json.reverse()
                name = record.name_get()
                path_names.append(name[0][1])
                path_json.append({
                    'model': record._name,
                    'name': name[0][1],
                    'id': isinstance(record.id, int) and record.id or 0,
                })
                record.update({
                    'path_names': '/'.join(path_names),
                    'path_json': json.dumps(path_json),
                })
            
    @api.depends('name')
    def _compute_extension(self):
        for record in self:
            record.extension = file.guess_extension(record.name)
     
    @api.depends('name')       
    def _compute_mimetype(self):
        for record in self: 
            mimetype = record.name and mimetypes.guess_type(record.name)[0]
            if not mimetype:
                binary = base64.b64decode(record.with_context({}).content or "")
                mimetype = guess_mimetype(binary, default='application/octet-stream')
            record.mimetype = mimetype
   
    @api.depends('content_binary')     
    def _compute_content(self):
        for record in self:
            record.content = record.content_binary
    
    @api.depends('content_binary') 
    def _compute_save_type(self):
        for record in self:
            record.save_type = "database"
    
    @api.depends('storage', 'storage.save_type') 
    def _compute_migration(self):
        storage_model = self.env['muk_dms.storage']
        save_field = storage_model._fields['save_type']
        values = save_field._description_selection(self.env)
        selection = {value[0]: value[1] for value in values}
        for record in self:
            storage_type = record.storage.save_type
            if storage_type != record.save_type:
                storage_label = selection.get(storage_type)
                file_label = selection.get(record.save_type)
                record.migration = "%s > %s" % (file_label, storage_label)
            else:
                record.migration = selection.get(storage_type)

    @api.multi
    def read(self, fields=None, load='_classic_read'):
        self.check_directory_access('read', {}, True)
        return super(File, self).read(fields, load=load)
    
    #----------------------------------------------------------
    # View
    #----------------------------------------------------------
    
    @api.onchange('category')
    def _change_category(self):
        res = {'domain': {
            'tags': [('category', '=', False)]
        }}
        if self.category:
            res.update({'domain': {
                'tags': ['|', 
                    ('category', '=', False),
                    ('category', 'child_of', self.category.id)
                ]
            }})
        tags = self.tags.filtered(
            lambda rec: not rec.category or \
            rec.category == self.category
        )
        self.tags = tags
        return res
        
    #----------------------------------------------------------
    # Security
    #----------------------------------------------------------
    
    @api.model
    def _get_directories_from_database(self, file_ids):
        if not file_ids:
            return self.env['muk_dms.directory']
        sql_query = '''
            SELECT directory 
            FROM muk_dms_file
            WHERE id = ANY (VALUES {ids});
        '''.format(
            ids=', '.join(map(lambda id: '(%s)' % id, file_ids))
        )
        self.env.cr.execute(sql_query, [])
        result = set(val[0] for val in self.env.cr.fetchall())
        return self.env['muk_dms.directory'].browse(result)
    
    @api.model
    def _read_group_process_groupby(self, gb, query):
        if self.env.user.id == SUPERUSER_ID or isinstance(self.env.uid, NoSecurityUid):
            return super(File, self)._read_group_process_groupby(gb, query)
        directories = self.env['muk_dms.directory'].with_context(prefetch_fields=False).search([])
        if directories:
            where_clause = '"{table}"."{field}" = ANY (VALUES {ids})'.format(
                table=self._table,
                field='directory',
                ids=', '.join(map(lambda id: '(%s)' % id, directories.ids)),
            )
            query.where_clause += [where_clause]
        else:
            query.where_clause += ['0=1']
        return super(File, self)._read_group_process_groupby(gb, query)

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        result = super(File, self)._search(args, offset, limit, order, False, access_rights_uid)
        if self.env.user.id == SUPERUSER_ID or isinstance(self.env.uid, NoSecurityUid):
            return len(result) if count else result
        if not result:
            return 0 if count else []
        file_ids = set(result)
        directories = self._get_directories_from_database(result)
        for directory in directories - directories._filter_access('read'):
            file_ids -= set(directory.sudo().mapped('files').ids)
        return len(file_ids) if count else list(file_ids)
    
    @api.multi
    def _filter_access(self, operation):
        records = super(File, self)._filter_access(operation)
        if self.env.user.id == SUPERUSER_ID or isinstance(self.env.uid, NoSecurityUid):
            return records
        directories = self._get_directories_from_database(records.ids)
        for directory in directories - directories._filter_access('read'):
            records -= self.browse(directory.sudo().mapped('files').ids)
        return records

    @api.multi
    def check_access(self, operation, raise_exception=False):
        res = super(File, self).check_access(operation, raise_exception)
        try:
            return res and self.check_directory_access(operation) == None
        except AccessError:
            if raise_exception:
                raise
            return False
        
    @api.multi
    def check_directory_access(self, operation, vals={}, raise_exception=False):
        if self.env.user.id == SUPERUSER_ID or isinstance(self.env.uid, NoSecurityUid):
            return None
        if 'directory' in vals and vals['directory']:
            records = self.env['muk_dms.directory'].browse(vals['directory'])
        else:
            records = self._get_directories_from_database(self.ids)
        return records.check_access(operation, raise_exception)

    #----------------------------------------------------------
    # Constrains
    #----------------------------------------------------------
    
    @api.constrains('name')
    def _check_name(self):
        for record in self:
            if not file.check_name(record.name):
                raise ValidationError(_("The file name is invalid."))
            files = record.sudo().directory.files.name_get()
            if list(filter(lambda file: file[1] == record.name and file[0] != record.id, files)):
                raise ValidationError(_("A file with the same name already exists."))
    
    @api.constrains('extension')
    def _check_extension(self):
        for record in self:
            if record.extension and record.extension in self._get_forbidden_extensions():
                raise ValidationError(_("The file has a forbidden file extension."))
    
    @api.constrains('size')
    def _check_size(self):
        for record in self:
            if record.size and record.size > self._get_binary_max_size() * 1024 * 1024:
                raise ValidationError(_("The maximum upload size is %s MB).") % self._get_binary_max_size())
    
    @api.constrains('directory')
    def _check_directory_access(self):
        for record in self:
            if not record.directory.check_access('create', raise_exception=False):
                raise ValidationError(_("The directory has to have the permission to create files."))
    
    #----------------------------------------------------------
    # Create, Update, Delete
    #----------------------------------------------------------
    
    @api.multi
    def _inverse_content(self):
        updates = defaultdict(set)
        for record in self:
            values = self._get_content_inital_vals()
            binary = base64.b64decode(record.content or "")
            values = self._update_content_vals(record, values, binary)
            values.update({
                'content_binary': record.content,
            })
            updates[tools.frozendict(values)].add(record.id)
        with self.env.norecompute():
            for vals, ids in updates.items():
                self.browse(ids).write(dict(vals))
        self.recompute()

    @api.multi
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or [])
        names = []
        if 'directory' in default:
            model = self.env['muk_dms.directory']
            directory = model.browse(default['directory']) 
            names = directory.sudo().files.mapped('name')
        else:
            names = self.sudo().directory.files.mapped('name')
        default.update({
            'name': file.unique_name(self.name, names, self.extension)
        })
        self.check_directory_access('create', default, True)
        return super(File, self).copy(default)
    
    @api.multi
    def write(self, vals):
        self.check_directory_access('write', vals, True)
        return super(File, self).write(vals)
    
    @api.multi
    def unlink(self):
        self.check_directory_access('unlink', {}, True)
        return super(File, self).unlink()