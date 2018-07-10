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

from odoo import models, api

_logger = logging.getLogger(__name__)

class DMSAccessModel(models.AbstractModel):
    
    _name = 'muk_dms.access'
    _description = "MuK Access Model"
    _inherit = 'muk_security.access_groups'
    
    _field_groups = 'muk_dms.group_dms_manager'
    _suspend_groups = 'muk_dms.group_dms_admin'
    
    #----------------------------------------------------------
    # Function
    #----------------------------------------------------------
    
    @api.multi
    def _eval_access_skip(self, operation):
        res = super(DMSAccessModel, self)._eval_access_skip(operation)
        if self.user_has_groups('muk_dms.group_dms_admin'):
            return True
        else:
            return res