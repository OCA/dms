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

import base64

from odoo import api, SUPERUSER_ID

def migrate(cr, version):
    if not version:
        return
    
    if version == "10.0.1.1.0":
        env = api.Environment(cr, SUPERUSER_ID, {})
        files = env["muk_dms.file"].search([("reference", "like", "data_database")])
        for file in files:
             file.trigger_computation(["extension","mimetype","index_content"])
             file.size = len(base64.b64decode(file.with_context({}).content))
        settingslist = env["muk_dms.settings"].search([("save_type", "=", "database")])
        for settings in settingslist:
            for root_directory in settings.root_directories:
                root_directory.trigger_computation(["path", "settings"])