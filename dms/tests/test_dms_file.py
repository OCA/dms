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

class FileTestCase(dms_case.DMSTestCase):
    
    def test_compute_thumbnail(self):
        file = self.browse_ref("muk_dms.file_14_demo")
        self.assertTrue(file.thumbnail)
        
    def test_create_file(self):
        directory = self.browse_ref("muk_dms.directory_12_demo")
        file = self.file.create({
            'name': "file.txt",
            'directory': directory.id,
            'content': self.file_base64()})
        self.assertTrue(file.extension == '.txt')
        
    def test_lock_file(self):
        file = self.browse_ref("muk_dms.file_14_demo")
        file.user_lock()
        self.assertTrue(file.is_locked_by())
        file.user_unlock()
        
    def test_unlink_file(self):
        directory = self.browse_ref("muk_dms.directory_12_demo")
        file = self.file.create({
            'name': "file.txt",
            'directory': directory.id,
            'content': self.file_base64()})
        file.unlink()
        self.assertFalse(file.exists())