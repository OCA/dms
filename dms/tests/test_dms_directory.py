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
import logging

from odoo.addons.muk_dms.tests import dms_case

_path = os.path.dirname(os.path.dirname(__file__))
_logger = logging.getLogger(__name__)

class DirectoryTestCase(dms_case.DMSTestCase):
    
    def test_compute_thumbnail(self):
        directory = self.browse_ref("muk_dms.directory_01_demo")
        self.assertTrue(directory.thumbnail)
        
    def test_create_directory(self):
        settings = self.browse_ref("muk_dms.settings_demo")
        root_directory = self.directory.create({
            'name': "RootTestDir",
            'is_root_directory': True,
            'settings': settings.id})
        self.assertTrue(root_directory.settings.id == settings.id)
        sub_directory = self.directory.create({
            'name': "SubTestDir",
            'is_root_directory': False,
            'parent_directory': root_directory.id})
        self.assertTrue(sub_directory.settings.id == settings.id)
        self.assertTrue(root_directory.count_directories == 1)
        
    def test_copy_root_directory(self):
        root_directory = self.browse_ref("muk_dms.directory_01_demo")
        copy_root_directory = root_directory.copy()
        self.assertTrue(root_directory.settings.id == copy_root_directory.settings.id)
        self.assertTrue(root_directory.count_directories == copy_root_directory.count_directories)
        self.assertTrue(root_directory.count_files  == copy_root_directory.count_files)
        copy_root_directory.unlink()
        
    def test_copy_sub_directory(self):
        sub_directory = self.browse_ref("muk_dms.directory_03_demo")
        copy_sub_directory = sub_directory.copy()
        self.assertTrue(sub_directory.settings.id == copy_sub_directory.settings.id)
        self.assertTrue(sub_directory.count_directories == copy_sub_directory.count_directories)
        self.assertTrue(sub_directory.count_files == copy_sub_directory.count_files)
        copy_sub_directory.unlink()
    
    def test_rename_directory(self):
        settings = self.browse_ref("muk_dms.settings_demo")
        root_directory = self.directory.create({
            'name': "RootTestDir",
            'is_root_directory': True,
            'settings': settings.id})
        sub_directory01 = self.directory.create({
            'name': "SubTestDir01",
            'is_root_directory': False,
            'parent_directory': root_directory.id})
        sub_directory02 = self.directory.create({
            'name': "SubTestDir02",
            'is_root_directory': False,
            'parent_directory': sub_directory01.id})
        sub_directory02_path = sub_directory02.path
        root_directory.write({'name': "RootTestDirNew"})
        self.assertFalse(sub_directory02_path  == sub_directory02.path)
    
    def test_unlink_directory(self):
        settings = self.browse_ref("muk_dms.settings_demo")
        root_directory = self.directory.create({
            'name': "RootTestDir",
            'is_root_directory': True,
            'settings': settings.id})
        sub_directory = self.directory.create({
            'name': "SubTestDir",
            'is_root_directory': False,
            'parent_directory': root_directory.id})
        root_directory.unlink()
        self.assertFalse(sub_directory.exists())