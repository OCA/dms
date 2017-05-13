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

import abc
import logging

from odoo import _
from odoo import models, api, fields
from odoo.exceptions import ValidationError, AccessError

_logger = logging.getLogger(__name__)

"""Commands"""
RENAME = 'rename'
REPLACE = 'replace'
MOVE = 'move'

class DataModel(models.AbstractModel):
    _name = 'muk_dms.data'
    _description = 'Base Data Model'
    
    @abc.abstractmethod
    def get_type(self):
        """Returns the data type."""
    
    @abc.abstractmethod
    def data(self):
        """Returns the data object."""
        
    @abc.abstractmethod
    def update(self, command, values):
        """Updated the data object."""
        
    @abc.abstractmethod
    def delete(self):
        """Deletes the data object."""
        
class DatabaseDataModel(models.Model):
    _name = 'muk_dms.database_data'
    _description = 'Database Data Model'
    
    _inherit = 'muk_dms.data'
    
    #----------------------------------------------------------
    # Database
    #----------------------------------------------------------
    
    file = fields.Binary(string="File")
    
    #----------------------------------------------------------
    # Abstract Implementation
    #----------------------------------------------------------
    
    def get_type(self):
        return "Database"
    
    def data(self):
        return self.file
    
    def update(self, command, values):
        if 'file' in values:
            self.file = values['file']
    
    def delete(self):
        self.file = None
    