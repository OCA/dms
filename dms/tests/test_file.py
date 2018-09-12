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

import os
import logging

from odoo.addons.muk_utils.tests.common import multi_users
from odoo.addons.muk_dms.tests.common import setup_data_function
from odoo.addons.muk_dms.tests.common import DocumentsBaseCase

_path = os.path.dirname(os.path.dirname(__file__))
_logger = logging.getLogger(__name__)

class FileTestCase(DocumentsBaseCase):
    
    def _setup_test_data(self):
        super(FileTestCase, self)._setup_test_data()
        self.directory_root_demo_01 = self.browse_ref("muk_dms.directory_01_demo")
        self.directory_root_demo_02 = self.browse_ref("muk_dms.directory_02_demo")
        self.directory_root_demo_03 = self.browse_ref("muk_dms.directory_03_demo")
        self.directory_sub_demo_01 = self.browse_ref("muk_dms.directory_11_demo")
        self.directory_sub_demo_02 = self.browse_ref("muk_dms.directory_12_demo")
        self.file_demo_01 = self.browse_ref("muk_dms.file_01_demo")
        self.file_demo_02 = self.browse_ref("muk_dms.file_02_demo")
        self.file_demo_03 = self.browse_ref("muk_dms.file_03_demo")
        self.file_demo_04 = self.browse_ref("muk_dms.file_04_demo")
        self.file_demo_05 = self.browse_ref("muk_dms.file_05_demo")
        self.new_storage = self.create_storage(sudo=True)
        self.new_root_directory = self.create_directory(storage=self.new_storage)
        self.new_sub_directory = self.create_directory(directory=self.new_root_directory)
        self.new_file_root_directory = self.create_file(directory=self.new_root_directory)
        self.new_file_sub_directory = self.create_file(directory=self.new_sub_directory)
        
    @multi_users(lambda self: self.multi_users())
    @setup_data_function(setup_func='_setup_test_data')
    def test_create_file(self):
        root_directory = self.create_directory(storage=self.new_storage)
        sub_directory = self.create_directory(directory=root_directory)
        file_root_directory = self.create_file(directory=root_directory)
        file_sub_directory = self.create_file(directory=sub_directory)
        self.assertTrue(root_directory.count_total_files == 2)
        self.assertTrue(sub_directory.count_files == 1)
        
    @multi_users(lambda self: self.multi_users())
    @setup_data_function(setup_func='_setup_test_data')
    def test_lock_file(self):
        file = self.create_file(sudo=True)
        file.sudo(self.env.uid).lock()
        self.assertTrue(file.is_locked)
        file.sudo(self.env.uid).unlock()
        self.assertFalse(file.is_locked)
    
    @multi_users(lambda self: self.multi_users())
    @setup_data_function(setup_func='_setup_test_data')
    def test_copy_file(self):
        copy_file = self.file_demo_01.copy()
        self.assertTrue(self.file_demo_01.storage.id == copy_file.storage.id)
        self.assertTrue(self.file_demo_01.content == copy_file.content)
        
    @multi_users(lambda self: self.multi_users())
    @setup_data_function(setup_func='_setup_test_data')
    def test_rename_file(self):
        file = self.create_file(sudo=True)
        extension = file.extension
        file.sudo(self.env.uid).write({'name': "Test.jpg"})
        self.assertFalse(file.extension == extension)
        
    @multi_users(lambda self: self.multi_users())
    @setup_data_function(setup_func='_setup_test_data')
    def test_move_file(self):
        path_names = self.file_demo_01.path_names
        self.file_demo_01.write({
            'directory': self.directory_root_demo_01.id,
        })
        self.assertFalse(path_names == self.file_demo_01.path_names)
        
    @multi_users(lambda self: self.multi_users())
    @setup_data_function(setup_func='_setup_test_data')
    def test_move_directory(self):
        path_names = self.directory_root_demo_03.files[0].path_names
        self.directory_root_demo_01.write({
            'root_storage': False,
            'is_root_directory': False,
            'parent_directory': self.directory_root_demo_02.id,
        })
        self.assertFalse(path_names == self.directory_root_demo_03.files[0].path_names)
        
    @multi_users(lambda self: self.multi_users())
    @setup_data_function(setup_func='_setup_test_data')
    def test_unlink_file(self):
        file = self.create_file(sudo=True)
        file.sudo(self.env.uid).unlink()
        self.assertFalse(file.exists())
        
    @multi_users(lambda self: self.multi_users())
    @setup_data_function(setup_func='_setup_test_data')
    def test_compute_thumbnail(self):
        self.assertTrue(self.file_demo_01.thumbnail)
        
    @multi_users(lambda self: self.multi_users())
    @setup_data_function(setup_func='_setup_test_data')
    def test_compute_path_names(self):
        self.assertTrue(self.file_demo_01.path_names)
        
    @multi_users(lambda self: self.multi_users())
    @setup_data_function(setup_func='_setup_test_data')
    def test_compute_path_json(self):
        self.assertTrue(self.file_demo_01.path_json)
        
    @multi_users(lambda self: self.multi_users())
    @setup_data_function(setup_func='_setup_test_data')
    def test_compute_mimetype(self):
        self.assertTrue(self.file_demo_01.mimetype)
        
    @multi_users(lambda self: self.multi_users())
    @setup_data_function(setup_func='_setup_test_data')
    def test_compute_extension(self):
        self.assertTrue(self.file_demo_01.extension)
        
    @multi_users(lambda self: self.multi_users())
    @setup_data_function(setup_func='_setup_test_data')
    def test_size_calculation(self):
        self.assertTrue(self.file_demo_01.size)
        
    @multi_users(lambda self: self.multi_users())
    @setup_data_function(setup_func='_setup_test_data')
    def test_checksum_calculation(self):
        self.assertTrue(self.file_demo_01.checksum)
        
    @multi_users(lambda self: self.multi_users())
    @setup_data_function(setup_func='_setup_test_data')
    def test_compute_content_bin_size(self):
        file = self.file_demo_01.with_context(bin_size=True)
        self.assertTrue(file.content)
        
    @multi_users(lambda self: self.multi_users())
    @setup_data_function(setup_func='_setup_test_data')
    def test_compute_content_base64(self):
        file = self.file_demo_01.with_context(bin_size=False)
        self.assertTrue(file.content)
        
    @multi_users(lambda self: self.multi_users())
    @setup_data_function(setup_func='_setup_test_data')
    def test_compute_save_type(self):
        self.assertTrue(self.file_demo_01.save_type)
        
    @multi_users(lambda self: self.multi_users())
    @setup_data_function(setup_func='_setup_test_data')
    def test_compute_migration(self):
        self.assertTrue(self.file_demo_01.migration)
        
    @multi_users(lambda self: self.multi_users())
    @setup_data_function(setup_func='_setup_test_data')
    def test_search_panel(self):
        self.assertTrue(self.file.search_panel_select_range('directory'))
        self.assertTrue(self.file.search_panel_select_multi_range('directory'))
        self.assertTrue(self.file.search_panel_select_multi_range('tags'))