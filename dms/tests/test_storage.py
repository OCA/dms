# Copyright 2017-2019 MuK IT GmbH.
# Copyright 2020 Creu Blanca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

from .common import multi_users
from .test_storage_database import StorageTestCase


class StorageLObjectTestCase(StorageTestCase):
    @multi_users(lambda self: self.multi_users(demo=False), callback="_setup_test_data")
    def test_file_migrate(self):
        storage = self.create_storage(sudo=False).with_user(self.uid)
        file_01 = self.create_file(storage=storage)
        self.assertEqual(file_01.storage_id, storage)
        self.assertEqual(file_01.storage_id.save_type, "database")
        self.assertEqual(file_01.save_type, "database")
        storage.write({"save_type": "file"})
        file_02 = self.create_file(storage=storage)
        self.assertEqual(file_01.storage_id, storage)
        self.assertEqual(file_01.storage_id.save_type, "file")
        self.assertEqual(file_01.save_type, "database")
        self.assertEqual(file_02.storage_id, storage)
        self.assertEqual(file_02.storage_id.save_type, "file")
        self.assertEqual(file_02.save_type, "file")
        storage.action_storage_migrate()
        self.assertEqual(file_01.storage_id, storage)
        self.assertEqual(file_01.storage_id.save_type, "file")
        self.assertEqual(file_01.save_type, "file")
        self.assertEqual(file_02.storage_id, storage)
        self.assertEqual(file_02.storage_id.save_type, "file")
        self.assertEqual(file_02.save_type, "file")
        storage.write({"save_type": "database"})
        storage.action_storage_migrate()
        self.assertEqual(file_01.storage_id, storage)
        self.assertEqual(file_01.storage_id.save_type, "database")
        self.assertEqual(file_01.save_type, "database")
        self.assertEqual(file_02.storage_id, storage)
        self.assertEqual(file_02.storage_id.save_type, "database")
        self.assertEqual(file_02.save_type, "database")
