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

from odoo import models, api, fields

_logger = logging.getLogger(__name__)

class Lock(models.Model):
    _name = 'muk_dms.lock'
    _description = "Directory or File Lock"

    name = fields.Char(
        compute='_compute_name',
        string="Name")

    locked_by = fields.Char(
        string="Locked by",
        required=True)
    
    locked_by_ref = fields.Reference(
        [('res.users', 'User')],
        string="User Reference")

    lock_ref = fields.Reference(
        [],
        string="Object Reference",
        required=True)
    
    token = fields.Char(
        string="Token")
    
    operation = fields.Char(
        string="Operation")
    
    @api.one
    @api.depends('lock_ref')
    def _compute_name(self):
        self.name = "Lock for " + str(self.lock_ref.name)