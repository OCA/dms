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

import logging

from odoo import _
from odoo import models, api, fields
from odoo.exceptions import ValidationError

from . import muk_dms_base as base

_logger = logging.getLogger(__name__)

"""Save Types"""
SAVE_DATABASE = "database"

class Root(base.DMSModel):
    _name = 'muk_dms.root'
    _description = "Root"
    
    _inherit = ['mail.thread']
    
    #----------------------------------------------------------
    # Database
    #----------------------------------------------------------
    
    name = fields.Char(string="Name", required=True)
    
    save_type = fields.Selection(selection='_get_save_types', string="Save Type", default="database",
                                 help="The save type is used to determine how a file is saved to the system.",
                                 required=True)
    
    root_directory = fields.Many2one('muk_dms.directory', string="Directory", required=True)
    
    is_created = fields.Boolean("Record is created", readonly=True)
    
    #----------------------------------------------------------
    # Local
    #----------------------------------------------------------
     
    save_types = [(SAVE_DATABASE, _('Database'))] 
    
    #----------------------------------------------------------
    # Functions
    #----------------------------------------------------------
    
    def _checking_lock(self):
        super(Root, self)._checking_lock()
        if self.root_directory.check_lock():
             raise AccessError(_("The record is locked, so it can't be changes or deleted."))
    
    def lock_subtree(self):
        self.root_directory.lock()
        self.lock()
            
    def unlock_subtree(self):
        self.root_directory.unlock()
        self.unlock()  
       
    #----------------------------------------------------------
    # Selections
    #----------------------------------------------------------
    
    def _get_save_types(self):
        return self.save_types
    
    #----------------------------------------------------------
    # Read, View 
    #----------------------------------------------------------
           
    @api.onchange('save_type') 
    def _onchange_save_type(self):
        if self.is_created:
            warning = {'title': (_('Warning')),
                       'message': (_('Changing the save type can cause a heavy migration process.')),}
            return {'warning':warning} 
        
    #----------------------------------------------------------
    # Create, Update
    #----------------------------------------------------------
    
    @api.one
    @api.constrains('root_directory')
    def _check_root_directory(self):
        _logger.debug("Checking directory constrains.")
        if not self.root_directory.is_root_direcotry():
            raise ValidationError(_("The selected directory must be a root directory."))
        root = self.root_directory.get_root()
        if root.id != self.id and root.check_existence():
            raise ValidationError(_("The selected directory has already a root. " +
                                  "Every directory tree can only have one corresponding root."))
            
    def _append_values_create(self, values):
        super(Root, self)._append_values_create(values)
        values['is_created'] = True
        return values