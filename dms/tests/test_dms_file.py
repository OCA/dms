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

import os
import base64
import logging
import unittest

from odoo import _
from odoo.tests import common

from odoo.addons.muk_dms.tests import dms_case

_path = os.path.dirname(os.path.dirname(__file__))
_logger = logging.getLogger(__name__)

class FileTestCase(dms_case.DMSTestCase):
    
    def setUp(self):
        super(FileTestCase, self).setUp()
        
    def tearDown(self):
        super(FileTestCase, self).tearDown()
    
    def test_create_file(self):
        directory = self.browse_ref("muk_dms.directory_12_demo").sudo()
        file = self.env['muk_dms.file'].sudo().create({
            'name': "file.txt",
            'directory': directory.id,
            'content': self.file_base64()})
        self.assertTrue(file.extension == '.txt')
        
    def test_compute_thumbnail(self):
        file = self.browse_ref("muk_dms.file_14_demo").sudo()
        self.assertTrue(file.thumbnail)
        
    def test_lock_file(self):
        file = self.browse_ref("muk_dms.file_14_demo").sudo()
        file.user_lock()
        self.assertTrue(file.is_locked_by())
        file.user_unlock()
        self.assertFalse(file.is_locked_by())
        
    def test_access_file(self):
        admin_file = self.browse_ref("muk_dms.file_14_demo").sudo()
        nouser_file = self.browse_ref("muk_dms.file_14_demo").sudo(self.demouser.id)
        self.assertTrue(admin_file.perm_read)
        self.assertTrue(admin_file.perm_create)
        self.assertTrue(admin_file.perm_write) 
        self.assertTrue(admin_file.perm_unlink)
        self.assertFalse(nouser_file.perm_read)
        self.assertFalse(nouser_file.perm_create)
        self.assertFalse(nouser_file.perm_write) 
        self.assertFalse(nouser_file.perm_unlink)
        
    def test_unlink_file(self):
        directory = self.browse_ref("muk_dms.directory_12_demo").sudo()
        file = self.env['muk_dms.file'].sudo().create({
            'name': "file.txt",
            'directory': directory.id,
            'content': self.file_base64()})
        file.unlink()
        self.assertFalse(file.exists())