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

class StorageTestCase(DocumentsBaseCase):
    
    def _setup_test_data(self):
        super(StorageTestCase, self)._setup_test_data()
        self.storage_demo = self.browse_ref("muk_dms.storage_demo")
        
    @multi_users(lambda self: self.multi_users(demo=False))
    @setup_data_function(setup_func='_setup_test_data')
    def test_action_storage_migrate(self):
        self.storage_demo.action_storage_migrate()
        
    @multi_users(lambda self: self.multi_users())
    @setup_data_function(setup_func='_setup_test_data')
    def test_count_storage_directories(self):
        self.assertTrue(self.storage_demo.count_storage_directories)
        
    @multi_users(lambda self: self.multi_users())
    @setup_data_function(setup_func='_setup_test_data')
    def test_count_storage_files(self):
        self.assertTrue(self.storage_demo.count_storage_files)
        
    