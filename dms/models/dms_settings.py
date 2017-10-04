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

import logging

from odoo import _
from odoo import models, api, fields
from odoo.exceptions import ValidationError, AccessError

from odoo.addons.muk_dms.models import dms_base

_logger = logging.getLogger(__name__)

class Settings(dms_base.DMSModel):
    _name = 'muk_dms.settings'
    _description = "MuK Documents Settings"

    #----------------------------------------------------------
    # Database
    #----------------------------------------------------------
    
    name = fields.Char(
        string="Name", 
        required=True)
    
    save_type = fields.Selection(
        selection=[("database", _('Database'))] , 
        string="Save Type", 
        default="database", 
        required=True,
        help="The save type is used to determine how a file is saved to the system.")
    
    index_files = fields.Boolean(
        string="Index Files", 
        default=True,
        help="Indicates if the file data should be indexed to allow faster and better search results.")
    
    system_locks = fields.Boolean(
        string="System Locks", 
        default=True,
        help="Indicates if files and directories should be automatically locked while system operations take place.")
    
    show_tree = fields.Boolean(
        string="Show Structure", 
        default=True,
        help="Indicates if directories inside of this settings object should be visible on document tree views.")
    
    settings_directories = fields.One2many(
        'muk_dms.directory', 
        'settings',
         string="Directories",
         copy=False, 
         readonly=True)
    
    settings_files = fields.One2many(
        'muk_dms.file', 
        'settings',
         string="Files",
         copy=False, 
         readonly=True)
    
    root_directories = fields.One2many(
        'muk_dms.directory',
         string="Root Directories",
         compute='_compute_root_directories')
    
    top_directories = fields.One2many(
        'muk_dms.directory',
         string="Top Directories",
         compute='_compute_top_directories',
         help="Directories which have no parent or the user has no access right to those parents.")
    
    top_files = fields.One2many(
        'muk_dms.file',
         string="Top Directories",
         compute='_compute_top_files',
         help="Files which parent aren't readable by the user.")
        
    #----------------------------------------------------------
    # Functions
    #----------------------------------------------------------
    
    def notify_change(self, values, refresh=False, operation=None):
        super(Settings, self).notify_change(values, refresh, operation)
        if self.system_locks:
                self.settings_directories.lock_tree(refresh=refresh, operation=operation)
        for directory in self.settings_directories:
            directory.with_context(operation=operation).notify_change(values)
        self.settings_directories.unlock_tree(refresh=refresh)
    
    #----------------------------------------------------------
    # Read, View 
    #----------------------------------------------------------
    
    @api.multi
    def _compute_root_directories(self):
        for record in self: 
            record.root_directories = record.sudo().settings_directories.filtered(
                lambda r: r.is_root_directory == True)
    
    @api.multi
    def _compute_top_directories(self):
        for record in self: 
            record.top_directories = record.settings_directories.filtered(
                lambda d: d.is_root_directory or not d.parent_directory.check_access('read'))
    
    @api.multi        
    def _compute_top_files(self):
        for record in self: 
            record.top_files = record.settings_files.filtered(
                lambda f: not f.directory.check_access('read'))
        
    #----------------------------------------------------------
    # Create, Update
    #----------------------------------------------------------
           
    @api.onchange('save_type', 'index_files') 
    def _onchange_save_type(self):
        if self._origin.id:
            warning = {
                'title': (_('Information')),
                'message': (_('Changing the settings can cause a heavy migration process.'))
            }
            return {'warning': warning} 
        
    def _after_write_record(self, vals, operation):
        vals = super(Settings, self)._after_write_record(vals, operation)
        self._check_notification(vals, operation)
        return vals
    
    def _check_notification(self, values, operation):
        if 'save_type' in values:
            self.notify_change({'save_type': values['save_type']}, operation=operation)
        if 'index_files' in values:
            self.notify_change({'index_files': values['index_files']}, operation=operation)