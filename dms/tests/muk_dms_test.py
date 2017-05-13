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

import os
import base64
import unittest

from odoo import _
from odoo.tests import common

_path = os.path.dirname(os.path.dirname(__file__))

class DMSTestCase(common.TransactionCase):
    
    at_install = True
    post_install = False
    
    def setUp(self):
        super(DMSTestCase, self).setUp()
        self.root_model = self.env['muk_dms.root'].sudo()
        self.dir_model = self.env['muk_dms.directory'].sudo()
        self.file_model = self.env['muk_dms.file'].sudo()
        self.lock_model = self.env['muk_dms.lock'].sudo()
        self.database_data_model = self.env['muk_dms.database_data'].sudo()
        
        self.manager = self.ref('base.user_root')
        self.user = self.ref('base.user_demo')
        
        self.root_model_manager = self.env['muk_dms.root'].sudo(self.manager)
        self.dir_model_manager = self.env['muk_dms.directory'].sudo(self.manager)
        self.file_model_manager = self.env['muk_dms.file'].sudo(self.manager)
        
        self.dir_model_user = self.env['muk_dms.directory'].sudo(self.user)
        self.file_model_user = self.env['muk_dms.file'].sudo(self.user)

        self.root_dir = self.dir_model.create({'name': 'Root_Directory'})
        self.root = self.root_model.create({'name': 'Database Settings', 'root_directory': self.root_dir.id, 'save_type': 'database'})
        
    def tearDown(self):
        super(DMSTestCase, self).tearDown()
    
    def _create_sample_file(self, dir=None):
        file = open(os.path.join(_path, 'static/demo/Sample.pdf'), 'r')
        file_read = file.read()
        return self.file_model.create({'directory': dir or self.root_dir.id, 'filename': 'Sample.pdf', 'file': base64.encodestring(file_read)})
    
    def _create_sample_file_access_manager(self, dir=None):
        file = open(os.path.join(_path, 'static/demo/Sample.pdf'), 'r')
        file_read = file.read()
        return self.file_model_manager.create({'directory': dir or self.root_dir.id, 'filename': 'Sample.pdf', 'file': base64.encodestring(file_read)})
        
    def _create_sample_file_access_user(self, dir=None):
        file = open(os.path.join(_path, 'static/demo/Sample.pdf'), 'r')
        file_read = file.read()
        return self.file_model_user.create({'directory': dir or self.root_dir.id, 'filename': 'Sample.pdf', 'file': base64.encodestring(file_read)})
        