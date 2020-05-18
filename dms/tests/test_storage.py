# Copyright 2017-2019 MuK IT GmbH.
# Copyright 2020 Creu Blanca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging
import os

from .common import DocumentsBaseCase, multi_users, setup_data_function

_path = os.path.dirname(os.path.dirname(__file__))
_logger = logging.getLogger(__name__)


class StorageTestCase(DocumentsBaseCase):
    def _setup_test_data(self):
        super(StorageTestCase, self)._setup_test_data()
        self.storage_demo = self.browse_ref("dms.storage_demo")

    @multi_users(lambda self: self.multi_users(demo=False))
    @setup_data_function(setup_func="_setup_test_data")
    def test_action_storage_migrate(self):
        self.storage_demo.action_storage_migrate()

    @multi_users(lambda self: self.multi_users())
    @setup_data_function(setup_func="_setup_test_data")
    def test_count_storage_directories(self):
        self.assertTrue(self.storage_demo.count_storage_directories)

    @multi_users(lambda self: self.multi_users())
    @setup_data_function(setup_func="_setup_test_data")
    def test_count_storage_files(self):
        self.assertTrue(self.storage_demo.count_storage_files)
