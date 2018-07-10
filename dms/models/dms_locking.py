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

class DMSLockingModel(models.AbstractModel):
    
    _name = 'muk_dms.locking'
    _description = 'MuK Document Locking Model'
    _inherit = ['muk_dms.model', 'muk_security.locking']

    #----------------------------------------------------------
    # Locking
    #----------------------------------------------------------

    @api.multi
    def lock(self, user=None, operation=None, *largs, **kwargs):
        res = super(DMSLockingModel, self).lock(user, operation, *largs, **kwargs)
        if "refresh" in kwargs and kwargs["refresh"]:
            self.refresh_views(model=self._name, ids=self.ids)
        return res
    
    @api.multi
    def unlock(self, *largs, **kwargs):
        res = super(DMSLockingModel, self).unlock(*largs, **kwargs)
        if "refresh" in kwargs and kwargs["refresh"]:
            self.refresh_views(model=self._name, ids=self.ids)
        return res
    
    @api.model
    def unlock_operation(self, operation, *largs, **kwargs):
        res = super(DMSLockingModel, self).unlock_operation(operation, *largs, **kwargs)
        if "refresh" in kwargs and kwargs["refresh"]:
            for tuple in res:
                self.refresh_views(model=tuple[0], ids=tuple[1])
        return res
    
    @api.multi
    def user_lock(self, *largs, **kwargs):
        res = super(DMSLockingModel, self).user_lock(*largs, **kwargs)
        self.refresh_views()
        return res
    
    @api.multi
    def user_unlock(self, *largs, **kwargs):
        res = super(DMSLockingModel, self).user_unlock(*largs, **kwargs)
        self.refresh_views()
        return res