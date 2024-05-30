# Copyright 2017-2019 MuK IT GmbH.
# Copyright 2020 Creu Blanca
# Copyright 2021-2022 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.exceptions import UserError
from odoo.tests.common import users
from odoo.tools import mute_logger

from .common import StorageDatabaseBaseCase


class FileDatabaseTestCase(StorageDatabaseBaseCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.file_demo_01 = cls.env.ref("dms.file_01_demo")
        cls.directory2 = cls.create_directory(storage=cls.storage)
        cls.new_storage2 = cls.create_storage(save_type="database")
        cls.directory3 = cls.create_directory(storage=cls.new_storage2)

    @users("dms-manager", "dms-user")
    def test_create_file(self):
        root_directory = self.create_directory(storage=self.storage)
        self.create_file(directory=root_directory)
        sub_directory = self.create_directory(directory=root_directory)
        self.create_file(sub_directory)
        self.assertEqual(root_directory.count_total_files, 2, "Total files should be 2")
        self.assertEqual(
            sub_directory.count_files, 1, "Subdirectory total files should be 1"
        )

    @users("dms-manager", "dms-user")
    def test_lock_file(self):
        file = self.create_file(directory=self.directory)
        file.lock()
        self.assertTrue(file.is_locked, "File should be locked")
        file.unlock()
        self.assertFalse(file.is_locked, "File should be unlocked")

    @users("dms-manager", "dms-user")
    def test_copy_file(self):
        copy_file = self.file.copy()
        self.assertEqual(
            self.file.storage_id, copy_file.storage_id, "Storage should be the same"
        )
        self.assertEqual(
            self.file.content, copy_file.content, "Content should be the same"
        )

    @users("dms-manager", "dms-user")
    def test_rename_file(self):
        file = self.create_file(directory=self.directory)
        extension = file.extension
        file.write({"name": "test-%s.jpg" % self.env.user.login})
        self.assertNotEqual(file.extension, extension, "Extension should be different")

    @users("dms-manager", "dms-user")
    def test_move_file(self):
        file = self.create_file(directory=self.directory)
        path_names = file.path_names
        file.write({"directory_id": self.directory2.id})
        file.flush_recordset()
        self.assertNotEqual(
            path_names, file.path_names, "Path names should be different"
        )

    @users("dms-manager", "dms-user")
    def test_move_directory(self):
        with self.assertRaises(
            UserError, msg="Directory can't have any parent, because it is " "root"
        ):
            self.directory.write(
                {
                    "is_root_directory": False,
                    "parent_id": self.directory3.id,
                }
            )

    @users("dms-manager", "dms-user")
    @mute_logger("odoo.models.unlink")
    def test_unlink_file(self):
        file = self.create_file(directory=self.directory)
        file.unlink()
        self.assertFalse(file.exists(), "File should not exist")

    @users("dms-manager", "dms-user")
    def test_compute_thumbnail(self):
        self.assertTrue(self.file_demo_01.image_128, "Thumbnail should be computed")

    @users("dms-manager", "dms-user")
    def test_compute_path_names(self):
        self.assertTrue(self.file.path_names, "Path names should be computed")

    @users("dms-manager", "dms-user")
    def test_compute_path_json(self):
        self.assertTrue(self.file.path_json, "Path json should be computed")

    @users("dms-manager", "dms-user")
    def test_compute_mimetype(self):
        self.assertTrue(self.file.mimetype, "Mimetype should be computed")

    @users("dms-manager", "dms-user")
    def test_compute_extension(self):
        self.assertTrue(self.file.extension, "Extension should be computed")

    @users("dms-manager", "dms-user")
    def test_size_calculation(self):
        self.assertTrue(self.file.size, "Size should be computed")

    @users("dms-manager", "dms-user")
    def test_checksum_calculation(self):
        self.assertTrue(self.file.checksum, "Checksum should be computed")

    @users("dms-manager", "dms-user")
    def test_compute_content(self):
        self.assertTrue(
            self.file.with_context(bin_size=True).content,
            "Content should be computed (with bin_size)",
        )
        self.assertTrue(
            self.file.with_context(bin_size=False).content,
            "Content should be computed (without bin_size)",
        )
        self.assertNotEqual(
            self.file.with_context(bin_size=False).content,
            self.file.with_context(bin_size=True).content,
            "Content should be different",
        )

    @users("dms-manager", "dms-user")
    def test_compute_save_type(self):
        self.assertTrue(self.file.save_type, "Save type should be computed")

    @users("dms-manager", "dms-user")
    def test_compute_migration(self):
        self.assertTrue(self.file.migration, "Migration should be computed")

    @users("dms-manager", "dms-user")
    def test_search_panel(self):
        self.assertTrue(
            self.file.search_panel_select_range("directory_id"),
            "Directory should be selected",
        )
        self.assertTrue(
            self.file.search_panel_select_multi_range("directory_id"),
            "Directory should be selected",
        )
        self.assertTrue(
            self.file.search_panel_select_multi_range("tag_ids"),
            "Tag should be selected",
        )
        res = self.file.search_panel_select_range("directory_id", enable_counters=True)
        self.assertTrue(self.directory2.id == x["id"] for x in res["values"])
