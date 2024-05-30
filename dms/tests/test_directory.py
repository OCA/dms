# Copyright 2017-2019 MuK IT GmbH.
# Copyright 2020 Creu Blanca
# Copyright 2021-2022 Tecnativa - Víctor Martínez
# Copyright 2024 Subteno - Timothée Vannier (https://www.subteno.com).
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import os

from odoo.exceptions import UserError
from odoo.tests.common import users
from odoo.tools import mute_logger

from .common import StorageDatabaseBaseCase

_path = os.path.dirname(os.path.dirname(__file__))


class DirectoryTestCaseBase(StorageDatabaseBaseCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.subdirectory = cls.create_directory(directory=cls.directory)
        cls.file.directory_id = cls.subdirectory
        cls.new_storage = cls.create_storage(save_type="database")

    @users("dms-manager", "dms-user")
    def test_create_directory(self):
        root_directory = self.create_directory(storage=self.storage)
        sub_directory = self.create_directory(directory=root_directory)
        self.assertEqual(
            sub_directory.storage_id.id,
            self.storage.id,
            msg="The storage of the subdirectory should be the same as "
            "the root directory",
        )
        self.assertEqual(
            root_directory.count_directories,
            1,
            msg="The root directory should have one subdirectory",
        )

    @users("dms-manager", "dms-user")
    def test_copy_root_directory(self):
        copy_root_directory = self.directory.copy()
        copy_root_directory.flush_recordset()
        self.assertEqual(
            self.directory.storage_id.id,
            copy_root_directory.storage_id.id,
            msg="The storage of the copied root directory should be the same as the "
            "original root directory",
        )
        self.assertEqual(
            self.directory.count_directories,
            copy_root_directory.count_directories,
            msg="The copied root directory should have the same number of "
            "subdirectories as the original root directory",
        )
        self.assertEqual(
            self.directory.count_files,
            copy_root_directory.count_files,
            msg="The copied root directory should have the same number of "
            "files as the original root directory",
        )

    @users("dms-manager", "dms-user")
    def test_copy_sub_directory(self):
        copy_sub_directory = self.subdirectory.copy()
        self.assertEqual(
            self.subdirectory.storage_id.id,
            copy_sub_directory.storage_id.id,
            msg="The storage of the copied subdirectory should be the same as the "
            "original subdirectory",
        )
        self.assertEqual(
            self.subdirectory.count_directories,
            copy_sub_directory.count_directories,
            msg="The copied subdirectory should have the same number of subdirectories "
            "as the original subdirectory",
        )
        self.assertEqual(
            self.subdirectory.count_files,
            copy_sub_directory.count_files,
            msg="The copied subdirectory should have the same number of "
            "files as the original subdirectory",
        )

    @users("dms-manager", "dms-user")
    def test_rename_directory(self):
        path_names = self.subdirectory.complete_name
        self.directory.write({"name": "New Test Name %s" % self.env.user.login})
        self.assertNotEqual(
            path_names,
            self.subdirectory.complete_name,
            msg="The path name of the subdirectory should have changed",
        )

    @users("dms-manager", "dms-user")
    def test_move_directory(self):
        with self.assertRaises(UserError, msg="The root directory should not be moved"):
            self.directory.write(
                {
                    "is_root_directory": False,
                    "parent_id": self.subdirectory.id,
                }
            )
        with self.assertRaises(
            UserError, msg="The subdirectory storage should not be changed"
        ):
            self.subdirectory.write(
                {
                    "is_root_directory": True,
                    "storage_id": self.new_storage.id,
                    "parent_id": False,
                }
            )
        self.subdirectory.write(
            {
                "is_root_directory": True,
                "storage_id": self.storage.id,
                "parent_id": False,
            }
        )
        new_directory = self.create_directory(storage=self.storage)
        self.subdirectory.write(
            {
                "is_root_directory": False,
                "storage_id": False,
                "parent_id": new_directory.id,
            }
        )
        with self.assertRaises(UserError, msg="The root directory should not be moved"):
            self.directory.storage_id = self.new_storage.id
            self.subdirectory.write(
                {
                    "is_root_directory": False,
                    "storage_id": False,
                    "parent_id": self.directory.id,
                }
            )

    @users("dms-manager", "dms-user")
    @mute_logger("odoo.models.unlink")
    def test_unlink_root_directory(self):
        root_directory = self.create_directory(storage=self.storage)
        sub_directory = self.create_directory(directory=root_directory)
        sub_files = self.create_file(directory=sub_directory)
        root_directory.unlink()
        self.assertFalse(
            sub_directory.exists(), msg="The subdirectory should not exist anymore"
        )
        self.assertFalse(
            sub_files.exists(), msg="The subfiles should not exist anymore"
        )

    @users("dms-manager", "dms-user")
    @mute_logger("odoo.models.unlink")
    def test_unlink_directory(self):
        root_directory = self.create_directory(storage=self.storage)
        sub_directory = self.create_directory(directory=root_directory)
        sub_files = self.create_file(directory=sub_directory)
        sub_directory.unlink()
        self.assertTrue(
            root_directory.exists(), msg="The root directory should still exist"
        )
        self.assertFalse(
            sub_files.exists(), msg="The subfiles should not exist anymore"
        )

    @users("dms-manager", "dms-user")
    def test_storage(self):
        root_directory = self.create_directory(storage=self.storage)
        sub_directory = self.create_directory(directory=root_directory)
        self.assertEqual(
            sub_directory.storage_id.id,
            self.storage.id,
            msg="The storage "
            "of the subdirectory should be the same as the root "
            "directory",
        )
        with self.assertRaises(
            UserError, msg="The storage of the root directory should " "not be changed"
        ):
            root_directory.write({"storage_id": self.new_storage.id})

    @users("dms-manager", "dms-user")
    def test_starred(self):
        self.directory.toggle_starred()
        self.subdirectory.write({"starred": True})
        starred = self.directory_model.search([("starred", "=", True)])
        self.assertIn(
            self.directory.id, starred.ids, msg="The directory should be starred"
        )
        self.assertIn(
            self.subdirectory.id, starred.ids, msg="The subdirectory should be starred"
        )

    @users("dms-manager", "dms-user")
    def test_count_directories(self):
        self.assertTrue(
            self.directory.count_directories,
            msg="The directory should have subdirectories",
        )

    @users("dms-manager", "dms-user")
    def test_count_files(self):
        self.assertTrue(
            self.subdirectory.count_files, msg="The subdirectory should have files"
        )

    @users("dms-manager", "dms-user")
    def test_count_elements(self):
        self.assertTrue(
            self.directory.count_elements,
            msg="The directory should have subdirectories and files",
        )

    @users("dms-manager", "dms-user")
    def test_count_total_directories(self):
        self.assertTrue(
            self.directory.count_total_directories,
            msg="The directory should have subdirectories",
        )

    @users("dms-manager", "dms-user")
    def test_count_count_total_files(self):
        self.assertTrue(
            self.directory.count_total_files, msg="The directory should have files"
        )

    @users("dms-manager", "dms-user")
    def test_count_total_elements(self):
        self.assertTrue(
            self.directory.count_total_elements,
            msg="The directory should have subdirectories and files",
        )

    @users("dms-manager", "dms-user")
    def test_size(self):
        self.assertTrue(self.directory.size, msg="The directory should have a size")

    @users("dms-manager", "dms-user")
    def test_name_get(self):
        directory = self.subdirectory.with_context(dms_directory_show_path=True)
        self.assertTrue(
            "/" in directory.with_context(dms_directory_show_path=True).display_name,
            msg="The path should be displayed in the directory name",
        )

    @users("dms-manager", "dms-user")
    def test_name_search(self):
        directories = self.directory_model.name_search("/")
        self.assertTrue(len(directories), msg="The root directory should be found")

    @users("dms-manager", "dms-user")
    def test_search_panel(self):
        self.assertTrue(
            self.directory_model.search_panel_select_multi_range("parent_id"),
            msg="The parent_id field should be a multi range field",
        )
        self.assertTrue(
            self.directory_model.search_panel_select_multi_range("category_id"),
            msg="The category_id field should be a multi range field",
        )
        self.assertTrue(
            self.directory_model.search_panel_select_multi_range("tag_ids"),
            msg="The tag_ids field should be a multi range field",
        )


class DirectoryMailTestCase(StorageDatabaseBaseCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.params = cls.env["ir.config_parameter"].sudo()
        cls.params.set_param("mail.catchall.domain", "dmstest.com")
        domain = cls.env["mail.alias.domain"].create({"name": "dmstest.com"})
        cls.env["mail.alias"].create(
            {
                "alias_model_id": cls.env["ir.model"]
                .search([("model", "=", "dms.directory")])
                .id,
                "alias_domain_id": domain.id,
            }
        )

    @mute_logger("odoo.addons.mail.mail_thread")
    def test_mail_alias_files(self):
        self.directory.write({"alias_process": "files", "alias_name": "directory+test"})
        self._handle_mail_reception()

    def _handle_mail_reception(self):
        with open(os.path.join(_path, "tests", "data", "mail01.eml")) as file:
            self.env["mail.thread"].message_process(None, file.read())
        with open(os.path.join(_path, "tests", "data", "mail02.eml")) as file:
            self.env["mail.thread"].message_process(None, file.read())

    @mute_logger("odoo.addons.mail.mail_thread")
    def test_mail_alias_directory(self):
        self.directory.write(
            {"alias_process": "directory", "alias_name": "directory+test"}
        )
        self._handle_mail_reception()
