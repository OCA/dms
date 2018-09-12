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

class DirectoryTestCase(DocumentsBaseCase):
    
    def _setup_test_data(self):
        super(DirectoryTestCase, self)._setup_test_data()
        self.directory_root_demo_01 = self.browse_ref("muk_dms.directory_01_demo")
        self.directory_root_demo_02 = self.browse_ref("muk_dms.directory_02_demo")
        self.directory_root_demo_03 = self.browse_ref("muk_dms.directory_11_demo")
        self.directory_sub_demo_01 = self.browse_ref("muk_dms.directory_03_demo")
        self.directory_sub_demo_02 = self.browse_ref("muk_dms.directory_12_demo")
        self.new_storage = self.create_storage(sudo=True)
    
    @multi_users(lambda self: self.multi_users())
    @setup_data_function(setup_func='_setup_test_data')
    def test_create_directory(self):
        root_directory = self.create_directory(storage=self.new_storage)
        sub_directory = self.create_directory(directory=root_directory)
        self.assertTrue(sub_directory.storage.id == self.new_storage.id)
        self.assertTrue(root_directory.count_directories == 1)
        
    @multi_users(lambda self: self.multi_users())
    @setup_data_function(setup_func='_setup_test_data')
    def test_copy_root_directory(self):
        copy_root_directory = self.directory_root_demo_03.copy()
        self.assertTrue(self.directory_root_demo_03.storage.id == copy_root_directory.storage.id)
        self.assertTrue(self.directory_root_demo_03.count_directories == copy_root_directory.count_directories)
        self.assertTrue(self.directory_root_demo_03.count_files  == copy_root_directory.count_files)
        
    @multi_users(lambda self: self.multi_users())
    @setup_data_function(setup_func='_setup_test_data')
    def test_copy_sub_directory(self):
        copy_sub_directory = self.directory_sub_demo_01.copy()
        self.assertTrue(self.directory_sub_demo_01.storage.id == copy_sub_directory.storage.id)
        self.assertTrue(self.directory_sub_demo_01.count_directories == copy_sub_directory.count_directories)
        self.assertTrue(self.directory_sub_demo_01.count_files == copy_sub_directory.count_files)
    
    @multi_users(lambda self: self.multi_users())
    @setup_data_function(setup_func='_setup_test_data')
    def test_rename_directory(self):
        path_names = self.directory_sub_demo_01.parent_path_names
        self.directory_root_demo_01.write({'name': "New Test Name"})
        self.assertFalse(path_names == self.directory_sub_demo_01.parent_path_names)
        
    @multi_users(lambda self: self.multi_users())
    @setup_data_function(setup_func='_setup_test_data')
    def test_move_directory(self):
        path_names = self.directory_sub_demo_01.parent_path_names
        self.directory_root_demo_01.write({
            'root_storage': False,
            'is_root_directory': False,
            'parent_directory': self.directory_root_demo_02.id,
        })
        self.assertFalse(path_names == self.directory_sub_demo_01.parent_path_names)
    
    @multi_users(lambda self: self.multi_users())
    @setup_data_function(setup_func='_setup_test_data')
    def test_unlink_directory(self):
        root_directory = self.create_directory(storage=self.new_storage)
        sub_directory = self.create_directory(directory=root_directory)
        sub_files = self.create_file(directory=sub_directory)
        root_directory.unlink()
        self.assertFalse(sub_directory.exists())
        self.assertFalse(sub_files.exists())
        
    @multi_users(lambda self: self.multi_users())
    @setup_data_function(setup_func='_setup_test_data')
    def test_storage(self):
        new_storage = self.create_storage(sudo=True)
        root_directory = self.create_directory(storage=self.new_storage)
        sub_directory = self.create_directory(directory=root_directory)
        self.assertTrue(sub_directory.storage.id == self.new_storage.id)
        root_directory.write({'root_storage': new_storage.id})
        self.assertTrue(sub_directory.storage.id == new_storage.id)
        
    @multi_users(lambda self: self.multi_users())
    @setup_data_function(setup_func='_setup_test_data')
    def test_starred(self):
        self.directory_root_demo_01.toggle_starred()
        self.directory_root_demo_02.write({'starred': True})
        starred = self.directory.search([('starred', '=', True)])
        self.assertTrue(self.directory_root_demo_01.id in starred.ids)
        self.assertTrue(self.directory_root_demo_02.id in starred.ids)

    @multi_users(lambda self: self.multi_users())
    @setup_data_function(setup_func='_setup_test_data')
    def test_count_directories(self):
        self.assertTrue(self.directory_root_demo_01.count_directories)

    @multi_users(lambda self: self.multi_users())
    @setup_data_function(setup_func='_setup_test_data')
    def test_count_files(self):
        self.assertTrue(self.directory_sub_demo_01.count_files)

    @multi_users(lambda self: self.multi_users())
    @setup_data_function(setup_func='_setup_test_data')
    def test_count_elements(self):
        self.assertTrue(self.directory_root_demo_01.count_elements)

    @multi_users(lambda self: self.multi_users())
    @setup_data_function(setup_func='_setup_test_data')
    def test_count_total_directories(self):
        self.assertTrue(self.directory_root_demo_01.count_total_directories)
        
    @multi_users(lambda self: self.multi_users())
    @setup_data_function(setup_func='_setup_test_data')
    def test_count_count_total_files(self):
        self.assertTrue(self.directory_root_demo_01.count_total_files)
        
    @multi_users(lambda self: self.multi_users())
    @setup_data_function(setup_func='_setup_test_data')
    def test_count_total_elements(self):
        self.assertTrue(self.directory_root_demo_01.count_total_elements)
        
    @multi_users(lambda self: self.multi_users())
    @setup_data_function(setup_func='_setup_test_data')
    def test_size(self):
        self.assertTrue(self.directory_root_demo_01.size)
        
    @multi_users(lambda self: self.multi_users())
    @setup_data_function(setup_func='_setup_test_data')
    def test_name_get(self):
        directory = self.directory_sub_demo_01.with_context(dms_directory_show_path=True)
        self.assertTrue("/" in directory.with_context(dms_directory_show_path=True).name_get()[0][1])
        
    @multi_users(lambda self: self.multi_users())
    @setup_data_function(setup_func='_setup_test_data')
    def test_name_search(self):
        directories = self.directory.name_search("/")
        self.assertTrue(len(directories))
        
    @multi_users(lambda self: self.multi_users())
    @setup_data_function(setup_func='_setup_test_data')
    def test_search_panel(self):
        self.assertTrue(self.directory.search_panel_select_multi_range('parent_directory'))
        self.assertTrue(self.directory.search_panel_select_multi_range('category'))
        self.assertTrue(self.directory.search_panel_select_multi_range('tags'))