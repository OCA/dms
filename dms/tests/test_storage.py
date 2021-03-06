# Copyright 2017-2019 MuK IT GmbH.
# Copyright 2020 Creu Blanca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

from .common import multi_users
from .test_storage_database import StorageTestCase


class StorageLObjectTestCase(StorageTestCase):
    @multi_users(lambda self: self.multi_users(demo=False), callback="_setup_test_data")
    def test_storage_attachment(self):
        model_res_partner = self.browse_ref("base.model_res_partner")
        res_partner_1 = self.browse_ref("base.res_partner_1").id
        storage = self.create_storage(sudo=False).with_user(self.uid)
        storage.write(
            {"save_type": "attachment", "model_ids": [(4, model_res_partner.id)]}
        )
        root_directory = self.create_directory(storage=storage, sudo=False).with_user(
            self.uid
        )
        root_directory.model_id = model_res_partner.id
        self.assertEqual(root_directory.res_model, model_res_partner.model)
        attachment = self.create_attachment(
            name="demo.txt",
            res_model=model_res_partner.model,
            res_id=res_partner_1,
            sudo=False,
        ).with_user(self.uid)
        self.assertEqual(root_directory.count_directories, 1)
        self.assertEqual(len(root_directory.child_directory_ids), 1)
        child_directory = root_directory.child_directory_ids[0]
        self.assertEqual(child_directory.res_model, model_res_partner.model)
        self.assertEqual(child_directory.res_id, res_partner_1)
        self.assertEqual(len(root_directory.child_directory_ids.file_ids), 1)
        dms_file = root_directory.child_directory_ids.file_ids[0]
        self.assertEqual(dms_file.attachment_id, attachment)
        self.assertEqual(dms_file.name, "demo.txt")
        self.assertEqual(dms_file.res_model, model_res_partner.model)
        self.assertEqual(dms_file.res_id, res_partner_1)
        directory_ids = self.directory.with_user(self.uid).search(
            [
                ("storage_id", "=", storage.id),
                ("res_model", "=", model_res_partner.model),
                ("res_id", "=", res_partner_1),
            ]
        )
        for directory_id in directory_ids:
            file_01 = self.create_file(
                directory=directory_id, storage=directory_id.storage_id,
            ).with_user(self.uid)
            self.assertEqual(file_01.res_model, model_res_partner.model)
            self.assertEqual(file_01.res_id, res_partner_1)
            self.assertEqual(file_01.storage_id, storage)
            self.assertEqual(file_01.storage_id.save_type, "attachment")
            self.assertEqual(file_01.save_type, "database")
            self.assertEqual(storage.count_storage_files, 2)

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
