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
import shutil
import logging
import tempfile

from odoo import models, api

from odoo.addons.muk_utils.tools import helper
from odoo.addons.muk_utils.tools import utils_os

_logger = logging.getLogger(__name__)

class DMSBaseModel(models.AbstractModel):
    
    _name = 'muk_dms.model'
    _description = 'MuK Document Base Model'
    _inherit = 'muk_utils.model'

    #----------------------------------------------------------
    # Function
    #----------------------------------------------------------
    
    @api.multi
    def notify_change(self, values, *largs, **kwargs):
        super(DMSBaseModel, self).notify_change(values, *largs, **kwargs)
        if "refresh" in kwargs and kwargs["refresh"]:
            self.refresh_views()
    
    @api.multi
    def trigger_computation(self, fields, *largs, **kwargs):
        super(DMSBaseModel, self).trigger_computation(fields, *largs, **kwargs)
        if "refresh" in kwargs and kwargs["refresh"]:
            self.refresh_views()
    
        
    @api.model
    def check_name(self, name):
        tmp_dir = tempfile.mkdtemp()
        try:
            open(os.path.join(tmp_dir, name), 'a').close()
        except IOError:
            return False
        finally:
            shutil.rmtree(tmp_dir)
        return True
    
    @api.model
    def unique_name(self, name, names, escape_suffix=False):
        return utils_os.unique_name(name, names, escape_suffix)
    
    @api.multi
    def refresh_views(self, model=None, ids=None, user=None, create=False):
        if self.exists() or ids:
            record = next(iter(self)) if len(self) > 1 else self
            self.env["bus.bus"].sendone("refresh", {
                "create": create if ids else record.exists() and record.create_date == record.write_date or False,
                "model": model or self._name,
                "uid": user and user.id or False if ids else self.env.user.id,
                "ids": ids or (record | self).mapped("id")})