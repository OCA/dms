# Copyright 2017-2019 MuK IT GmbH.
# Copyright 2020 Creu Blanca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from .common import DocumentsBaseCase, multi_users


class StorageTestCase(DocumentsBaseCase):
    def _setup_test_data(self):
        self.storage_demo = self.browse_ref("dms.storage_demo")

    @multi_users(lambda self: self.multi_users(demo=False), callback="_setup_test_data")
    def test_action_storage_migrate(self):
        self.storage_demo.sudo(self.uid).action_storage_migrate()

    @multi_users(lambda self: self.multi_users(), callback="_setup_test_data")
    def test_count_storage_directories(self):
        self.assertTrue(self.storage_demo.count_storage_directories)

    @multi_users(lambda self: self.multi_users(), callback="_setup_test_data")
    def test_count_storage_files(self):
        self.assertTrue(self.storage_demo.count_storage_files)
