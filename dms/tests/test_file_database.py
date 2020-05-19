# Copyright 2017-2019 MuK IT GmbH.
# Copyright 2020 Creu Blanca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from .common import DocumentsBaseCase, multi_users


class FileTestCase(DocumentsBaseCase):
    def _setup_test_data(self):
        super(FileTestCase, self)._setup_test_data()
        self.directory_root_demo_01 = self.browse_ref("dms.directory_01_demo")
        self.directory_root_demo_02 = self.browse_ref("dms.directory_02_demo")
        self.directory_root_demo_03 = self.browse_ref("dms.directory_03_demo")
        self.directory_sub_demo_01 = self.browse_ref("dms.directory_11_demo")
        self.directory_sub_demo_02 = self.browse_ref("dms.directory_12_demo")
        self.file_demo_01 = self.browse_ref("dms.file_01_demo")
        self.file_demo_02 = self.browse_ref("dms.file_02_demo")
        self.file_demo_03 = self.browse_ref("dms.file_03_demo")
        self.file_demo_04 = self.browse_ref("dms.file_04_demo")
        self.file_demo_05 = self.browse_ref("dms.file_05_demo")
        self.new_storage = self.create_storage(sudo=True)
        self.new_root_directory = self.create_directory(storage=self.new_storage)
        self.new_sub_directory = self.create_directory(
            directory=self.new_root_directory
        )
        self.new_file_root_directory = self.create_file(
            directory=self.new_root_directory
        )
        self.new_file_sub_directory = self.create_file(directory=self.new_sub_directory)

    @multi_users(lambda self: self.multi_users(), callback="_setup_test_data")
    def test_create_file(self):
        root_directory = self.create_directory(storage=self.new_storage)
        self.create_file(root_directory)
        sub_directory = self.create_directory(directory=root_directory)
        self.create_file(sub_directory)
        self.assertEqual(root_directory.count_total_files, 2)
        self.assertEqual(sub_directory.count_files, 1)

    @multi_users(lambda self: self.multi_users(), callback="_setup_test_data")
    def test_lock_file(self):
        file = self.create_file(sudo=True)
        file.with_user(self.env.uid).lock()
        self.assertTrue(file.is_locked)
        file.with_user(self.env.uid).unlock()
        self.assertFalse(file.is_locked)

    @multi_users(lambda self: self.multi_users(), callback="_setup_test_data")
    def test_copy_file(self):
        copy_file = self.file_demo_01.copy()
        self.assertEqual(self.file_demo_01.storage_id, copy_file.storage_id)
        self.assertEqual(self.file_demo_01.content, copy_file.content)

    @multi_users(lambda self: self.multi_users(), callback="_setup_test_data")
    def test_rename_file(self):
        file = self.create_file(sudo=True)
        extension = file.extension
        file.with_user(self.env.uid).write({"name": "Test.jpg"})
        self.assertNotEqual(file.extension, extension)

    @multi_users(lambda self: self.multi_users(), callback="_setup_test_data")
    def test_move_file(self):
        path_names = self.file_demo_01.path_names
        self.file_demo_01.write({"directory_id": self.directory_root_demo_01.id})
        self.file_demo_01.flush()
        self.assertNotEqual(path_names, self.file_demo_01.path_names)

    @multi_users(lambda self: self.multi_users(), callback="_setup_test_data")
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

    @multi_users(lambda self: self.multi_users(), callback="_setup_test_data")
    def test_unlink_file(self):
        file = self.create_file(sudo=True)
        file.with_user(self.env.uid).unlink()
        self.assertFalse(file.exists())

    @multi_users(lambda self: self.multi_users(), callback="_setup_test_data")
    def test_compute_thumbnail(self):
        self.assertTrue(self.file_demo_01.thumbnail)

    @multi_users(lambda self: self.multi_users(), callback="_setup_test_data")
    def test_compute_path_names(self):
        self.assertTrue(self.file_demo_01.path_names)

    @multi_users(lambda self: self.multi_users(), callback="_setup_test_data")
    def test_compute_path_json(self):
        self.assertTrue(self.file_demo_01.path_json)

    @multi_users(lambda self: self.multi_users(), callback="_setup_test_data")
    def test_compute_mimetype(self):
        self.assertTrue(self.file_demo_01.res_mimetype)

    @multi_users(lambda self: self.multi_users(), callback="_setup_test_data")
    def test_compute_extension(self):
        self.assertTrue(self.file_demo_01.extension)

    @multi_users(lambda self: self.multi_users(), callback="_setup_test_data")
    def test_size_calculation(self):
        self.assertTrue(self.file_demo_01.size)

    @multi_users(lambda self: self.multi_users(), callback="_setup_test_data")
    def test_checksum_calculation(self):
        self.assertTrue(self.file_demo_01.checksum)

    @multi_users(lambda self: self.multi_users(), callback="_setup_test_data")
    def test_compute_content(self):
        self.assertTrue(self.file_demo_01.with_context(bin_size=True).content)
        self.assertTrue(self.file_demo_01.with_context(bin_size=False).content)
        self.assertNotEqual(
            self.file_demo_01.with_context(bin_size=False).content,
            self.file_demo_01.with_context(bin_size=True).content,
        )

    @multi_users(lambda self: self.multi_users(), callback="_setup_test_data")
    def test_compute_save_type(self):
        self.assertTrue(self.file_demo_01.save_type)

    @multi_users(lambda self: self.multi_users(), callback="_setup_test_data")
    def test_compute_migration(self):
        self.assertTrue(self.file_demo_01.migration)

    @multi_users(lambda self: self.multi_users(), callback="_setup_test_data")
    def test_search_panel(self):
        self.assertTrue(self.file.search_panel_select_range("directory_id"))
        self.assertTrue(self.file.search_panel_select_multi_range("directory_id"))
        self.assertTrue(self.file.search_panel_select_multi_range("tag_ids"))
