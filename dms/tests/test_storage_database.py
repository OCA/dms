# Copyright 2017-2019 MuK IT GmbH.
# Copyright 2020 Creu Blanca
# Copyright 2020 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from .common import DocumentsBaseCase


class StorageTestCase(DocumentsBaseCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.storage_demo = cls.env.ref("dms.storage_demo")

    def test_action_storage_migrate(self):
        self.storage_demo.with_user(self.admin_uid).action_storage_migrate()

    def test_count_storage_directories(self):
        self.assertTrue(
            self.storage_demo.with_user(self.admin_uid).count_storage_directories
        )

    def test_count_storage_files(self):
        self.assertTrue(self.storage_demo.with_user(self.admin_uid).count_storage_files)
