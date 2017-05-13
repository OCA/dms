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

from . import muk_dms_test as dms_test

_path = os.path.dirname(os.path.dirname(__file__))

class DataTestCase(dms_test.DMSTestCase):
    
    def test_create_file(self):
        file_res = open(os.path.join(_path, 'static/demo/Sample.pdf'), 'r')
        file_read = file_res.read()
        file = self.file_model.create({'directory': self.root_dir.id, 'filename': 'Sample.pdf', 'file': base64.encodestring(file_read)})
        self.assertTrue(file.file_ref)
        self.assertEqual(file.get_file_data(), base64.encodestring(file_read))
    
    def test_delete_file(self):
        file_res = open(os.path.join(_path, 'static/demo/Sample.pdf'), 'r')
        file_read = file_res.read()
        file = self.file_model.create({'directory': self.root_dir.id, 'filename': 'Sample.pdf', 'file': base64.encodestring(file_read)})
        size = len(self.database_data_model.search([]))
        file.unlink()
        self.assertTrue(size > len(self.database_data_model.search([])))