# Copyright 2017-2019 MuK IT GmbH.
# Copyright 2020 Creu Blanca
# Copyright 2021-2022 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import os

from odoo.exceptions import UserError
from odoo.tests.common import users
from odoo.tools import mute_logger

from .common import StorageDatabaseBaseCase

_path = os.path.dirname(os.path.dirname(__file__))


class DirectoryTestCase(StorageDatabaseBaseCase):
    def setUp(self):
        super().setUp()
        self.subdirectory = self.create_directory(directory=self.directory)
        self.file.directory_id = self.subdirectory
        self.new_storage = self.create_storage(save_type="database")

    @users("dms-manager", "dms-user")
    def test_create_directory(self):
        root_directory = self.create_directory(storage=self.storage)
        sub_directory = self.create_directory(directory=root_directory)
        self.assertEqual(sub_directory.storage_id.id, self.storage.id)
        self.assertEqual(root_directory.count_directories, 1)

    @users("dms-manager", "dms-user")
    def test_copy_root_directory(self):
        copy_root_directory = self.directory.copy()
        copy_root_directory.flush()
        self.assertEqual(
            self.directory.storage_id.id, copy_root_directory.storage_id.id
        )
        self.assertEqual(
            self.directory.count_directories,
            copy_root_directory.count_directories,
        )
        self.assertEqual(self.directory.count_files, copy_root_directory.count_files)

    @users("dms-manager", "dms-user")
    def test_copy_sub_directory(self):
        copy_sub_directory = self.subdirectory.copy()
        self.assertEqual(
            self.subdirectory.storage_id.id, copy_sub_directory.storage_id.id
        )
        self.assertEqual(
            self.subdirectory.count_directories,
            copy_sub_directory.count_directories,
        )
        self.assertEqual(self.subdirectory.count_files, copy_sub_directory.count_files)

    @users("dms-manager", "dms-user")
    def test_rename_directory(self):
        path_names = self.subdirectory.complete_name
        self.directory.write({"name": "New Test Name %s" % self.env.user.login})
        self.assertNotEqual(path_names, self.subdirectory.complete_name)

    @users("dms-manager", "dms-user")
    def test_move_directory(self):
        with self.assertRaises(UserError):
            self.directory.write(
                {
                    "is_root_directory": False,
                    "parent_id": self.subdirectory.id,
                }
            )

    @users("dms-manager", "dms-user")
    def test_unlink_root_directory(self):
        root_directory = self.create_directory(storage=self.storage)
        sub_directory = self.create_directory(directory=root_directory)
        sub_files = self.create_file(directory=sub_directory)
        root_directory.unlink()
        self.assertFalse(sub_directory.exists())
        self.assertFalse(sub_files.exists())

    @users("dms-manager", "dms-user")
    def test_unlink_directory(self):
        root_directory = self.create_directory(storage=self.storage)
        sub_directory = self.create_directory(directory=root_directory)
        sub_files = self.create_file(directory=sub_directory)
        sub_directory.unlink()
        self.assertTrue(root_directory.exists())
        self.assertFalse(sub_files.exists())

    @users("dms-manager", "dms-user")
    def test_storage(self):
        root_directory = self.create_directory(storage=self.storage)
        sub_directory = self.create_directory(directory=root_directory)
        self.assertEqual(sub_directory.storage_id.id, self.storage.id)
        with self.assertRaises(UserError):
            root_directory.write({"storage_id": self.new_storage.id})

    @users("dms-manager", "dms-user")
    def test_starred(self):
        self.directory.toggle_starred()
        self.subdirectory.write({"starred": True})
        starred = self.directory_model.search([("starred", "=", True)])
        self.assertIn(self.directory.id, starred.ids)
        self.assertIn(self.subdirectory.id, starred.ids)

    @users("dms-manager", "dms-user")
    def test_count_directories(self):
        self.assertTrue(self.directory.count_directories)

    @users("dms-manager", "dms-user")
    def test_count_files(self):
        self.assertTrue(self.subdirectory.count_files)

    @users("dms-manager", "dms-user")
    def test_count_elements(self):
        self.assertTrue(self.directory.count_elements)

    @users("dms-manager", "dms-user")
    def test_count_total_directories(self):
        self.assertTrue(self.directory.count_total_directories)

    @users("dms-manager", "dms-user")
    def test_count_count_total_files(self):
        self.assertTrue(self.directory.count_total_files)

    @users("dms-manager", "dms-user")
    def test_count_total_elements(self):
        self.assertTrue(self.directory.count_total_elements)

    @users("dms-manager", "dms-user")
    def test_size(self):
        self.assertTrue(self.directory.size)

    @users("dms-manager", "dms-user")
    def test_name_get(self):
        directory = self.subdirectory.with_context(dms_directory_show_path=True)
        self.assertTrue(
            "/" in directory.with_context(dms_directory_show_path=True).name_get()[0][1]
        )

    @users("dms-manager", "dms-user")
    def test_name_search(self):
        directories = self.directory_model.name_search("/")
        self.assertTrue(len(directories))

    @users("dms-manager", "dms-user")
    def test_search_panel(self):
        self.assertTrue(
            self.directory_model.search_panel_select_multi_range("parent_id")
        )
        self.assertTrue(
            self.directory_model.search_panel_select_multi_range("category_id")
        )
        self.assertTrue(self.directory_model.search_panel_select_multi_range("tag_ids"))


class DirectoryMailTestCase(DirectoryTestCase):
    def setUp(self):
        super().setUp()
        self.params = self.env["ir.config_parameter"].sudo()
        self.params.set_param("mail.catchall.domain", "mydomain.com")

    @mute_logger("odoo.addons.mail.mail_thread")
    def test_mail_alias_files(self):
        self.directory.write({"alias_process": "files", "alias_name": "directory+test"})
        with open(os.path.join(_path, "tests", "data", "mail01.eml"), "r") as file:
            self.env["mail.thread"].message_process(None, file.read())
        with open(os.path.join(_path, "tests", "data", "mail02.eml"), "r") as file:
            self.env["mail.thread"].message_process(None, file.read())

    @mute_logger("odoo.addons.mail.mail_thread")
    def test_mail_alias_directory(self):
        self.directory.write(
            {"alias_process": "directory", "alias_name": "directory+test"}
        )
        with open(os.path.join(_path, "tests", "data", "mail01.eml"), "r") as file:
            self.env["mail.thread"].message_process(None, file.read())
        with open(os.path.join(_path, "tests", "data", "mail02.eml"), "r") as file:
            self.env["mail.thread"].message_process(None, file.read())
