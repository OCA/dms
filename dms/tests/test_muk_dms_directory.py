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

class DirectoryTestCase(dms_test.DMSTestCase):
    
    at_install = False
    post_install = True
    
    def test_create_sub_directory(self):
        sub_dir = self.dir_model.create({'name': 'New_Directory', 'parent_id': self.root_dir.id})
        self._create_sample_file(sub_dir.id)
        self.assertEqual(sub_dir.parent_id, self.root_dir)
        self.assertEqual(sub_dir.get_root(), self.root)
        self.assertTrue(len(self.root_dir.child_id) == 1)
        
    def test_move_directory(self):
        sub_dir_1 = self.dir_model.create({'name': '1_Directory', 'parent_id': self.root_dir.id})
        sub_dir_2 = self.dir_model.create({'name': '2_Directory', 'parent_id': self.root_dir.id})
        self._create_sample_file(sub_dir_1.id)
        self._create_sample_file(sub_dir_2.id)
        self.assertEqual(sub_dir_1.path_text, 'Root_Directory/1_Directory/')
        self.assertEqual(sub_dir_2.path_text, 'Root_Directory/2_Directory/')
        self.assertTrue(len(sub_dir_1.child_id) == 0)
        self.assertTrue(len(sub_dir_2.child_id) == 0)
        sub_dir_2.write({'parent_id': sub_dir_1.id})
        self.assertEqual(sub_dir_1.path_text, 'Root_Directory/1_Directory/')
        self.assertEqual(sub_dir_2.path_text, 'Root_Directory/1_Directory/2_Directory/')
        self.assertTrue(len(sub_dir_1.child_id) == 1)
        self.assertTrue(len(sub_dir_2.child_id) == 0)
        
    def test_create_sub_directory_access_manager(self):
        sub_dir = self.dir_model_manager.create({'name': 'New_Directory', 'parent_id': self.root_dir.id})
        self._create_sample_file_access_manager(sub_dir.id)
        self.assertEqual(sub_dir.parent_id, self.root_dir)
        self.assertEqual(sub_dir.get_root(), self.root)
        self.assertTrue(len(self.root_dir.child_id) == 1)
        
    def test_move_directory_access_manager(self):
        sub_dir_1 = self.dir_model_manager.create({'name': '1_Directory', 'parent_id': self.root_dir.id})
        sub_dir_2 = self.dir_model_manager.create({'name': '2_Directory', 'parent_id': self.root_dir.id})
        self._create_sample_file_access_manager(sub_dir_1.id)
        self._create_sample_file_access_manager(sub_dir_2.id)
        self.assertEqual(sub_dir_1.path_text, 'Root_Directory/1_Directory/')
        self.assertEqual(sub_dir_2.path_text, 'Root_Directory/2_Directory/')
        self.assertTrue(len(sub_dir_1.child_id) == 0)
        self.assertTrue(len(sub_dir_2.child_id) == 0)
        sub_dir_2.write({'parent_id': sub_dir_1.id})
        self.assertEqual(sub_dir_1.path_text, 'Root_Directory/1_Directory/')
        self.assertEqual(sub_dir_2.path_text, 'Root_Directory/1_Directory/2_Directory/')
        self.assertTrue(len(sub_dir_1.child_id) == 1)
        self.assertTrue(len(sub_dir_2.child_id) == 0)
        
    def test_create_sub_directory_access_user(self):
        sub_dir = self.dir_model_user.create({'name': 'New_Directory', 'parent_id': self.root_dir.id})
        self._create_sample_file_access_user(sub_dir.id)
        self.assertEqual(sub_dir.parent_id, self.root_dir)
        self.assertEqual(sub_dir.get_root(), self.root)
        self.assertTrue(len(self.root_dir.child_id) == 1)
        
    def test_move_directory_access_user(self):
        sub_dir_1 = self.dir_model_user.create({'name': '1_Directory', 'parent_id': self.root_dir.id})
        sub_dir_2 = self.dir_model_user.create({'name': '2_Directory', 'parent_id': self.root_dir.id})
        self._create_sample_file_access_user(sub_dir_1.id)
        self._create_sample_file_access_user(sub_dir_2.id)
        self.assertEqual(sub_dir_1.path_text, 'Root_Directory/1_Directory/')
        self.assertEqual(sub_dir_2.path_text, 'Root_Directory/2_Directory/')
        self.assertTrue(len(sub_dir_1.child_id) == 0)
        self.assertTrue(len(sub_dir_2.child_id) == 0)
        sub_dir_2.write({'parent_id': sub_dir_1.id})
        self.assertEqual(sub_dir_1.path_text, 'Root_Directory/1_Directory/')
        self.assertEqual(sub_dir_2.path_text, 'Root_Directory/1_Directory/2_Directory/')
        self.assertTrue(len(sub_dir_1.child_id) == 1)
        self.assertTrue(len(sub_dir_2.child_id) == 0)
        