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

import logging
import textwrap

from odoo import _, models, api, fields
from odoo.exceptions import AccessError

_logger = logging.getLogger(__name__)

class Storage(models.Model):
    
    _name = 'muk_dms.storage'
    _description = "Storage"
    
    #----------------------------------------------------------
    # Database
    #----------------------------------------------------------
    
    name = fields.Char(
        string="Name", 
        required=True)
    
    save_type = fields.Selection(
        selection=[("database", _('Database'))], 
        string="Save Type", 
        default="database", 
        required=True,
        help="""The save type is used to determine how a file is saved by the system. If you change 
            this setting, you can migrate existing files manually by triggering the action.""")
    
    company = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.user.company_id,
        help="If set, directories and files will only be available for the selected company.")

    is_hidden = fields.Boolean(
        string="Storage is Hidden", 
        default=False,
        help="Indicates if directories and files are hidden by default.")
     
    root_directories = fields.One2many(
        comodel_name='muk_dms.directory',
        inverse_name='root_storage',
        string="Root Directories",
        auto_join=False,
        readonly=False,
        copy=False)
         
    storage_directories = fields.One2many(
        comodel_name='muk_dms.directory', 
        inverse_name='storage',
        string="Directories",
        auto_join=False,
        readonly=True,
        copy=False)
     
    storage_files = fields.One2many(
        comodel_name='muk_dms.file', 
        inverse_name='storage',
        string="Files",
        auto_join=False,
        readonly=True,
        copy=False)
     
    count_storage_directories = fields.Integer(
        compute='_compute_count_storage_directories',
        string="Count Directories")
     
    count_storage_files = fields.Integer(
        compute='_compute_count_storage_files',
        string="Count Files")
    
    #----------------------------------------------------------
    # Actions
    #----------------------------------------------------------
    
    @api.multi
    def action_storage_migrate(self):
        if not self.env.user.has_group('muk_dms.group_dms_manager'):
            raise AccessError(_('Only managers can execute this action.'))
        files = self.env['muk_dms.file'].with_context(active_test=False).sudo()
        for record in self:
            domain = ['&', ('content_binary', '=', False), ('storage', '=', record.id)]
            files |= files.search(domain)
        files.action_migrate()

    @api.multi
    def action_save_onboarding_storage_step(self):
        self.env.user.company_id.set_onboarding_step_done(
            'documents_onboarding_storage_state'
        )
    
    #----------------------------------------------------------
    # Read, View 
    #----------------------------------------------------------
    
    @api.depends('storage_directories')
    def _compute_count_storage_directories(self):
        for record in self:
            record.count_storage_directories = len(record.storage_directories)
    
    @api.depends('storage_files')
    def _compute_count_storage_files(self):
        for record in self:
            record.count_storage_files = len(record.storage_files)
        