# Copyright 2017-2019 MuK IT GmbH.
# Copyright 2020 Creu Blanca
# Copyright 2021 Víctor Martínez
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

from .common import multi_users
from .test_storage_database import StorageTestCase


class StorageLObjectTestCase(StorageTestCase):
    def setUp(self):
        super().setUp()
        self.model_res_partner = self.browse_ref("base.model_res_partner")
        self.partner = self.browse_ref("base.res_partner_12")

    @multi_users(lambda self: self.multi_users(demo=False), callback="_setup_test_data")
    def test_file_migrate(self):
        storage = self.create_storage(sudo=False).sudo(self.uid)
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
        storage.write({"save_type": "attachment"})
        directory = self.directory.create(
            {
                "name": self.model_res_partner.model,
                "root_storage_id": storage.id,
                "is_root_directory": True,
                "model_id": self.model_res_partner.id,
            }
        )
        file_03 = self.create_file_with_context(
            context={
                "default_res_model": self.model_res_partner.model,
                "default_res_id": self.partner.id,
            },
            directory=directory,
            storage=storage,
        )
        self.assertEqual(file_02.storage_id, storage)
        self.assertEqual(file_02.storage_id.save_type, "attachment")
        self.assertEqual(file_02.save_type, "database")
        self.assertEqual(file_03.storage_id, storage)
        self.assertEqual(file_03.storage_id.save_type, "attachment")
        self.assertEqual(file_03.save_type, "file")
        storage.action_storage_migrate()
        self.assertEqual(file_02.storage_id, storage)
        self.assertEqual(file_02.storage_id.save_type, "attachment")
        self.assertEqual(file_02.save_type, "file")
        self.assertEqual(file_03.storage_id, storage)
        self.assertEqual(file_03.storage_id.save_type, "attachment")
        self.assertEqual(file_03.save_type, "file")
