# Copyright 2017-2019 MuK IT GmbH.
# Copyright 2020 Creu Blanca
# Copyright 2022 Víctor Martínez
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.tests.common import users
from odoo.tools import mute_logger

from .common import StorageDatabaseBaseCase


class StorageDatabaseTestCase(StorageDatabaseBaseCase):
    @users("dms-manager")
    def test_action_storage_migrate(self):
        self.storage.action_storage_migrate()

    @users("dms-manager", "dms-user")
    def test_count_storage_directories(self):
        self.assertTrue(
            self.storage.count_storage_directories, "Storage should have directories"
        )

    @users("dms-manager", "dms-user")
    def test_count_storage_files(self):
        self.assertTrue(self.storage.count_storage_files, "Storage should have files")

    @users("dms-manager")
    @mute_logger("odoo.models.unlink")
    def test_file_migrate(self):
        root_directory = self.storage.root_directory_ids.filtered(
            lambda x: x.is_root_directory
        )
        file_01 = self.create_file(directory=root_directory)
        self.assertEqual(
            file_01.storage_id, self.storage, "File should be in the storage"
        )
        self.assertEqual(
            file_01.storage_id.save_type, "database", "Storage should be database"
        )
        self.assertEqual(
            file_01.save_type, "database", "File savetype should be database"
        )
        self.storage.write({"save_type": "file"})
        directory = self.create_directory(storage=self.storage)
        file_02 = self.create_file(directory=directory)
        self.assertEqual(
            file_01.storage_id, self.storage, "File should be in the storage"
        )
        self.assertEqual(file_01.storage_id.save_type, "file", "Storage should be file")
        self.assertEqual(
            file_01.save_type, "database", "File savetype should be database"
        )
        self.assertEqual(
            file_02.storage_id, self.storage, "File should be in the storage"
        )
        self.assertEqual(file_02.storage_id.save_type, "file", "Storage should be file")
        self.assertEqual(file_02.save_type, "file", "File savetype should be file")
        self.storage.action_storage_migrate()
        self.assertEqual(
            file_01.storage_id, self.storage, "File should be in the storage"
        )
        self.assertEqual(file_01.storage_id.save_type, "file", "Storage should be file")
        self.assertEqual(file_01.save_type, "file", "File savetype should be file")
        self.assertEqual(
            file_02.storage_id, self.storage, "File should be in the storage"
        )
        self.assertEqual(file_02.storage_id.save_type, "file", "Storage should be file")
        self.assertEqual(file_02.save_type, "file", "File savetype should be file")
        self.storage.write({"save_type": "database"})
        self.storage.action_storage_migrate()
        self.assertEqual(
            file_01.storage_id, self.storage, "File should be in the storage"
        )
        self.assertEqual(
            file_01.storage_id.save_type, "database", "Storage should be database"
        )
        self.assertEqual(
            file_01.save_type, "database", "File savetype should be database"
        )
        self.assertEqual(
            file_02.storage_id, self.storage, "File should be in the storage"
        )
        self.assertEqual(
            file_02.storage_id.save_type, "database", "Storage should be database"
        )
        self.assertEqual(
            file_02.save_type, "database", "File savetype should be database"
        )
        self.storage.write({"save_type": "attachment"})
        model_partner = self.env.ref("base.model_res_partner")
        partner = self.partner_model.create({"name": "Test partner"})
        directory = self.directory_model.create(
            {
                "name": self.partner_model._name,
                "model_id": model_partner.id,
                "res_id": partner.id,
                "parent_id": self.storage.root_directory_ids[0].id,
                "storage_id": self.storage.id,
            }
        )
        file_03 = self.create_file(directory=directory)
        self.assertEqual(
            file_02.storage_id, self.storage, "File should be in the storage"
        )
        self.assertEqual(
            file_02.storage_id.save_type, "attachment", "Storage should be attachment"
        )
        self.assertEqual(
            file_02.save_type, "database", "File savetype should be database"
        )
        self.assertEqual(
            file_03.storage_id, self.storage, "File should be in the storage"
        )
        self.assertEqual(
            file_03.storage_id.save_type, "attachment", "Storage should be attachment"
        )
        self.assertEqual(
            file_03.save_type, "database", "File savetype should be database"
        )
        self.storage.action_storage_migrate()
        self.assertEqual(
            file_02.storage_id, self.storage, "File should be in the storage"
        )
        self.assertEqual(
            file_02.storage_id.save_type, "attachment", "Storage should be attachment"
        )
        self.assertEqual(
            file_02.save_type, "database", "File savetype should be database"
        )
        self.assertEqual(
            file_03.storage_id, self.storage, "File should be in the storage"
        )
        self.assertEqual(
            file_03.storage_id.save_type, "attachment", "Storage should be attachment"
        )
        self.assertEqual(
            file_03.save_type, "database", "File savetype should be database"
        )
