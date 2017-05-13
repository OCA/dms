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

class FileTestCase(dms_test.DMSTestCase):
    
    def test_create_file(self):
        file = self._create_sample_file()
        self.assertEqual(file.link_preview, '/dms/file/preview?id=%s' % file.id)
        self.assertEqual(file.link_download, '/dms/file/download/%s' % file.id)
        self.assertEqual(file.link_checkout, '/dms/file/checkout/%s' % file.id)
        self.assertEqual(file.link_update, '/dms/file/update/%s' % file.id)
        self.assertEqual(file.name, 'Sample')
        self.assertEqual(file.file_extension, '.pdf')
        self.assertEqual(file.mime_type, 'application/pdf')
        self.assertEqual(file.file_size, 1420)
        self.assertEqual(file.type.lower(), 'database')
        self.assertEqual(file.type.lower(), self.root.save_type.lower())
        self.assertEqual(file.path_text, 'Root_Directory/')
        self.assertEqual(file.path_text, '%s/' % self.root_dir.name)
        self.assertEqual(file.is_locked_flag, False)
    
    @unittest.expectedFailure
    def test_create_file_invalid_name(self):
        file = open(os.path.join(_path, 'static/demo/Sample.pdf'), 'r')
        file_read = file.read()
        self.file_model.create({'directory': self.root_dir.id, 'filename': 'Sa/mple.pdf', 'file': base64.encodestring(file_read)})
        
    @unittest.expectedFailure    
    def test_create_file_duplicate(self):
        file = self._create_sample_file()
        file = self._create_sample_file()
        
    def test_lock_file(self):
        file = self._create_sample_file()
        lock = file.user_lock()
        self.assertEqual(file.is_editor, True)
        self.assertEqual(file.is_locked_flag, True)
        self.assertEqual(lock[0][0]['record'], file)
        self.assertEqual(lock[0][0]['lock'].locked_by_ref.id, self.env.user.id)
        file.user_unlock()
        self.assertEqual(file.is_locked_flag, False)
    
    @unittest.expectedFailure     
    def test_lock_file_edit(self):
        file = self._create_sample_file()
        file.user_lock()
        file.write({'filename': 'NewName'})
        
    def test_copy_file(self):
        file = self._create_sample_file()
        file_copy = file.copy()
        self.assertEqual(file_copy.name, _("Copy of ") + file.name)
        
    def test_write_file(self):
        file = self._create_sample_file()
        file_res = open(os.path.join(_path, 'static/demo/Sample.doc'), 'r')
        file_read = file_res.read()
        file.write({'filename': 'Sample.doc', 'file': base64.encodestring(file_read)})
        self.assertEqual(file.filename, 'Sample.doc')
        self.assertEqual(file.file_extension, '.doc')
        self.assertEqual(file.mime_type, 'application/msword')
        self.assertEqual(file.file_size, 756)
    
    def test_move_file(self):
        file = self._create_sample_file()
        self.assertEqual(file.path_text, 'Root_Directory/')
        dir = self.dir_model.create({'name': 'New_Directory', 'parent_id': self.root_dir.id})
        file.write({'directory': dir.id})
        self.assertEqual(file.path_text, 'Root_Directory/New_Directory/')
        
    def test_delete_file(self):
        file = self._create_sample_file()
        size = len(self.file_model.search([]))
        file.unlink()
        self.assertTrue(size > len(self.file_model.search([])))

    def test_create_file_access_manager(self):
        file = self._create_sample_file_access_manager()
        self.assertEqual(file.link_preview, '/dms/file/preview?id=%s' % file.id)
        self.assertEqual(file.link_download, '/dms/file/download/%s' % file.id)
        self.assertEqual(file.link_checkout, '/dms/file/checkout/%s' % file.id)
        self.assertEqual(file.link_update, '/dms/file/update/%s' % file.id)
        self.assertEqual(file.name, 'Sample')
        self.assertEqual(file.file_extension, '.pdf')
        self.assertEqual(file.mime_type, 'application/pdf')
        self.assertEqual(file.file_size, 1420)
        self.assertEqual(file.type.lower(), 'database')
        self.assertEqual(file.type.lower(), self.root.save_type.lower())
        self.assertEqual(file.path_text, 'Root_Directory/')
        self.assertEqual(file.path_text, '%s/' % self.root_dir.name)
        self.assertEqual(file.is_locked_flag, False)
        
    def test_lock_file_access_manager(self):
        file = self._create_sample_file_access_manager()
        lock = file.user_lock()
        self.assertEqual(file.is_editor, True)
        self.assertEqual(file.is_locked_flag, True)
        self.assertEqual(lock[0][0]['record'], file)
        self.assertEqual(lock[0][0]['lock'].locked_by_ref.id, self.manager)
        file.user_unlock()
        self.assertEqual(file.is_locked_flag, False)
    
    def test_copy_file_access_manager(self):
        file = self._create_sample_file_access_manager()
        file_copy = file.copy()
        self.assertEqual(file_copy.name, _("Copy of ") + file.name)
        
    def test_write_file_access_manager(self):
        file = self._create_sample_file_access_manager()
        file_res = open(os.path.join(_path, 'static/demo/Sample.doc'), 'r')
        file_read = file_res.read()
        file.write({'filename': 'Sample.doc', 'file': base64.encodestring(file_read)})
        self.assertEqual(file.filename, 'Sample.doc')
        self.assertEqual(file.file_extension, '.doc')
        self.assertEqual(file.mime_type, 'application/msword')
        self.assertEqual(file.file_size, 756)
    
    def test_move_file_access_manager(self):
        file = self._create_sample_file_access_manager()
        self.assertEqual(file.path_text, 'Root_Directory/')
        dir = self.dir_model.create({'name': 'New_Directory', 'parent_id': self.root_dir.id})
        file.write({'directory': dir.id})
        self.assertEqual(file.path_text, 'Root_Directory/New_Directory/')
        
    def test_delete_file_access_manager(self):
        file = self._create_sample_file_access_manager()
        size = len(self.file_model.search([]))
        file.unlink()
        self.assertTrue(size > len(self.file_model.search([])))
        
    def test_create_file_access_user(self):
        file = self._create_sample_file_access_user()
        self.assertEqual(file.link_preview, '/dms/file/preview?id=%s' % file.id)
        self.assertEqual(file.link_download, '/dms/file/download/%s' % file.id)
        self.assertEqual(file.link_checkout, '/dms/file/checkout/%s' % file.id)
        self.assertEqual(file.link_update, '/dms/file/update/%s' % file.id)
        self.assertEqual(file.name, 'Sample')
        self.assertEqual(file.file_extension, '.pdf')
        self.assertEqual(file.mime_type, 'application/pdf')
        self.assertEqual(file.file_size, 1420)
        self.assertEqual(file.type.lower(), 'database')
        self.assertEqual(file.type.lower(), self.root.save_type.lower())
        self.assertEqual(file.path_text, 'Root_Directory/')
        self.assertEqual(file.path_text, '%s/' % self.root_dir.name)
        self.assertEqual(file.is_locked_flag, False)
        
    def test_lock_file_access_user(self):
        file = self._create_sample_file_access_user()
        lock = file.user_lock()
        self.assertEqual(file.is_editor, True)
        self.assertEqual(file.is_locked_flag, True)
        self.assertEqual(lock[0][0]['record'], file)
        self.assertEqual(lock[0][0]['lock'].locked_by_ref.id, self.user)
        file.user_unlock()
        self.assertEqual(file.is_locked_flag, False)
    
    def test_copy_file_access_user(self):
        file = self._create_sample_file_access_user()
        file_copy = file.copy()
        self.assertEqual(file_copy.name, _("Copy of ") + file.name)
        
    def test_write_file_access_user(self):
        file = self._create_sample_file_access_user()
        file_res = open(os.path.join(_path, 'static/demo/Sample.doc'), 'r')
        file_read = file_res.read()
        file.write({'filename': 'Sample.doc', 'file': base64.encodestring(file_read)})
        self.assertEqual(file.filename, 'Sample.doc')
        self.assertEqual(file.file_extension, '.doc')
        self.assertEqual(file.mime_type, 'application/msword')
        self.assertEqual(file.file_size, 756)
    
    def test_move_file_access_user(self):
        file = self._create_sample_file_access_user()
        self.assertEqual(file.path_text, 'Root_Directory/')
        dir = self.dir_model.create({'name': 'New_Directory', 'parent_id': self.root_dir.id})
        file.write({'directory': dir.id})
        self.assertEqual(file.path_text, 'Root_Directory/New_Directory/')
        
    def test_delete_file_access_user(self):
        file = self._create_sample_file_access_user()
        size = len(self.file_model.search([]))
        file.unlink()
        self.assertTrue(size > len(self.file_model.search([])))        