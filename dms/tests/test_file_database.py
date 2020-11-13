# Copyright 2017-2019 MuK IT GmbH.
# Copyright 2020 Creu Blanca
# Copyright 2020 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from .common import DocumentsBaseCase


class FileTestCase(DocumentsBaseCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.directory_root_demo_01 = cls.env.ref("dms.directory_01_demo")
        cls.directory_root_demo_02 = cls.env.ref("dms.directory_02_demo")
        cls.directory_root_demo_03 = cls.env.ref("dms.directory_03_demo")
        cls.directory_sub_demo_01 = cls.env.ref("dms.directory_11_demo")
        cls.directory_sub_demo_02 = cls.env.ref("dms.directory_12_demo")
        cls.file_demo_01 = cls.env.ref("dms.file_01_demo")
        cls.file_demo_02 = cls.env.ref("dms.file_02_demo")
        cls.file_demo_03 = cls.env.ref("dms.file_03_demo")
        cls.file_demo_04 = cls.env.ref("dms.file_04_demo")
        cls.file_demo_05 = cls.env.ref("dms.file_05_demo")
        cls.new_storage = cls.create_storage(cls, sudo=True).with_user(cls.admin_uid)
        cls.new_root_directory = cls.create_directory(
            cls, storage=cls.new_storage
        ).with_user(cls.admin_uid)
        cls.new_sub_directory = cls.create_directory(
            cls, directory=cls.new_root_directory
        ).with_user(cls.admin_uid)
        cls.new_file_root_directory = cls.create_file(
            cls, directory=cls.new_root_directory
        ).with_user(cls.admin_uid)
        cls.new_file_sub_directory = cls.create_file(
            cls, directory=cls.new_sub_directory
        ).with_user(cls.admin_uid)

    def test_create_file(self):
        root_directory = self.create_directory(storage=self.new_storage).with_user(
            self.admin_uid
        )
        self.create_file(root_directory).with_user(self.admin_uid)
        sub_directory = self.create_directory(directory=root_directory).with_user(
            self.admin_uid
        )
        self.create_file(sub_directory).with_user(self.admin_uid)
        self.assertEqual(root_directory.count_total_files, 2)
        self.assertEqual(sub_directory.count_files, 1)

    def test_lock_file(self):
        file = self.create_file(sudo=True).with_user(self.admin_uid)
        file.with_user(self.admin_uid).lock()
        self.assertTrue(file.is_locked)
        file.with_user(self.admin_uid).unlock()
        self.assertFalse(file.is_locked)

    def test_copy_file(self):
        copy_file = self.file_demo_01.copy().with_user(self.admin_uid)
        self.assertEqual(self.file_demo_01.storage_id, copy_file.storage_id)
        self.assertEqual(self.file_demo_01.content, copy_file.content)

    def test_rename_file(self):
        file = self.create_file(sudo=True).with_user(self.admin_uid)
        extension = file.extension
        file.with_user(self.admin_uid).write({"name": "Test.jpg"})
        self.assertNotEqual(file.extension, extension)

    def test_move_file(self):
        path_names = self.file_demo_01.path_names
        self.file_demo_01.write({"directory_id": self.directory_root_demo_01.id})
        self.file_demo_01.flush()
        self.assertNotEqual(path_names, self.file_demo_01.path_names)

    def test_move_directory(self):
        file = self.directory_root_demo_03.file_ids[0]
        path_names = file.path_names
        self.directory_root_demo_01.write(
            {
                "root_storage_id": False,
                "is_root_directory": False,
                "parent_id": self.directory_root_demo_02.id,
            }
        )
        self.directory_root_demo_01.flush()
        # We need to refresh as the field is not stored
        file.refresh()
        self.assertNotEqual(path_names, file.path_names)

    def test_unlink_file(self):
        file = self.create_file(sudo=True).with_user(self.admin_uid)
        file.with_user(self.admin_uid).unlink()
        self.assertFalse(file.exists())

    def test_compute_thumbnail(self):
        self.assertTrue(self.file_demo_01.thumbnail)

    def test_compute_path_names(self):
        self.assertTrue(self.file_demo_01.path_names)

    def test_compute_path_json(self):
        self.assertTrue(self.file_demo_01.path_json)

    def test_compute_mimetype(self):
        self.assertTrue(self.file_demo_01.res_mimetype)

    def test_compute_extension(self):
        self.assertTrue(self.file_demo_01.extension)

    def test_size_calculation(self):
        self.assertTrue(self.file_demo_01.size)

    def test_checksum_calculation(self):
        self.assertTrue(self.file_demo_01.checksum)

    def test_compute_content(self):
        self.assertTrue(self.file_demo_01.with_context(bin_size=True).content)
        self.assertTrue(self.file_demo_01.with_context(bin_size=False).content)
        self.assertNotEqual(
            self.file_demo_01.with_context(bin_size=False).content,
            self.file_demo_01.with_context(bin_size=True).content,
        )

    def test_compute_save_type(self):
        self.assertTrue(self.file_demo_01.save_type)

    def test_compute_migration(self):
        self.assertTrue(self.file_demo_01.migration)

    def test_search_panel(self):
        self.assertTrue(self.file.search_panel_select_range("directory_id"))
        self.assertTrue(self.file.search_panel_select_multi_range("directory_id"))
        self.assertTrue(self.file.search_panel_select_multi_range("tag_ids"))
