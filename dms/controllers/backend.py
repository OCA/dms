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

from odoo import _, http
from odoo.http import request

_logger = logging.getLogger(__name__)

class BackendController(http.Controller):

    @http.route('/config/muk_dms.forbidden_extensions', type='json', auth="user")
    def forbidden_extensions(self, **kw):
        params = request.env['ir.config_parameter'].sudo()
        return {
            'forbidden_extensions': params.get_param("muk_dms.forbidden_extensions", default="")
        }