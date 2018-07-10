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

from odoo import models, api, fields

_logger = logging.getLogger(__name__)
        
class DatabaseDataModel(models.Model):
    
    _name = 'muk_dms.data_database'
    _description = 'Database Data Model'
    _inherit = 'muk_dms.data'
    
    #----------------------------------------------------------
    # Database
    #----------------------------------------------------------
    
    data = fields.Binary(
        string="Content")
    
    #----------------------------------------------------------
    # Abstract Implementation
    #----------------------------------------------------------
    
    @api.multi
    def type(self):
        return "database"
    
    @api.multi
    def content(self):
        self.ensure_one()
        return self.data
    
    @api.multi
    def update(self, values):
        if 'content' in values:
            self.write({'data': values['content']})