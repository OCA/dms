# Copyright 2017-2019 MuK IT GmbH.
# Copyright 2020 Creu Blanca
# Copyright 2021-2022 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.exceptions import UserError
from odoo.tests.common import users

from .common import StorageDatabaseBaseCase


class FileDatabaseTestCase(StorageDatabaseBaseCase):
    def setUp(self):
        super().setUp()
        self.file_demo_01 = self.env.ref("dms.file_01_demo")
        self.directory2 = self.create_directory(storage=self.storage)

    @users("dms-manager", "dms-user")
    def test_create_file(self):
        root_directory = self.create_directory(storage=self.storage)
        self.create_file(directory=root_directory)
        sub_directory = self.create_directory(directory=root_directory)
        self.create_file(sub_directory)
        self.assertEqual(root_directory.count_total_files, 2)
        self.assertEqual(sub_directory.count_files, 1)

    @users("dms-manager", "dms-user")
    def test_lock_file(self):
        file = self.create_file(directory=self.directory)
        file.lock()
        self.assertTrue(file.is_locked)
        file.unlock()
        self.assertFalse(file.is_locked)

    @users("dms-manager", "dms-user")
    def test_copy_file(self):
        copy_file = self.file.copy()
        self.assertEqual(self.file.storage_id, copy_file.storage_id)
        self.assertEqual(self.file.content, copy_file.content)

    @users("dms-manager", "dms-user")
    def test_rename_file(self):
        file = self.create_file(directory=self.directory)
        extension = file.extension
        file.write({"name": "test-%s.jpg" % self.env.user.login})
        self.assertNotEqual(file.extension, extension)

    @users("dms-manager", "dms-user")
    def test_move_file(self):
        file = self.create_file(directory=self.directory)
        path_names = file.path_names
        file.write({"directory_id": self.directory2.id})
        file.flush()
        self.assertNotEqual(path_names, file.path_names)

    @users("dms-manager", "dms-user")
    def test_move_directory(self):
        with self.assertRaises(UserError):
            self.directory.write(
                {
                    "is_root_directory": False,
                    "parent_id": self.directory2.id,
                }
            )

    @users("dms-manager", "dms-user")
    def test_unlink_file(self):
        file = self.create_file(directory=self.directory)
        file.unlink()
        self.assertFalse(file.exists())

    @users("dms-manager", "dms-user")
    def test_compute_thumbnail(self):
        self.assertTrue(self.file_demo_01.image_128)

    @users("dms-manager", "dms-user")
    def test_compute_path_names(self):
        self.assertTrue(self.file.path_names)

    @users("dms-manager", "dms-user")
    def test_compute_path_json(self):
        self.assertTrue(self.file.path_json)

    @users("dms-manager", "dms-user")
    def test_compute_mimetype(self):
        self.assertTrue(self.file.mimetype)

    @users("dms-manager", "dms-user")
    def test_compute_extension(self):
        self.assertTrue(self.file.extension)

    @users("dms-manager", "dms-user")
    def test_size_calculation(self):
        self.assertTrue(self.file.size)

    @users("dms-manager", "dms-user")
    def test_checksum_calculation(self):
        self.assertTrue(self.file.checksum)

    @users("dms-manager", "dms-user")
    def test_compute_content(self):
        self.assertTrue(self.file.with_context(bin_size=True).content)
        self.assertTrue(self.file.with_context(bin_size=False).content)
        self.assertNotEqual(
            self.file.with_context(bin_size=False).content,
            self.file.with_context(bin_size=True).content,
        )

    @users("dms-manager", "dms-user")
    def test_compute_save_type(self):
        self.assertTrue(self.file.save_type)

    @users("dms-manager", "dms-user")
    def test_compute_migration(self):
        self.assertTrue(self.file.migration)

    @users("dms-manager", "dms-user")
    def test_search_panel(self):
        self.assertTrue(self.file.search_panel_select_range("directory_id"))
        self.assertTrue(self.file.search_panel_select_multi_range("directory_id"))
        self.assertTrue(self.file.search_panel_select_multi_range("tag_ids"))
