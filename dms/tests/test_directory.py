# Copyright 2017-2019 MuK IT GmbH.
# Copyright 2020 Creu Blanca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from .common import DocumentsBaseCase, multi_users


class DirectoryTestCase(DocumentsBaseCase):
    def _setup_test_data(self):
        super(DirectoryTestCase, self)._setup_test_data()
        self.directory_root_demo_01 = self.browse_ref("dms.directory_01_demo")
        self.directory_root_demo_02 = self.browse_ref("dms.directory_02_demo")
        self.directory_root_demo_03 = self.browse_ref("dms.directory_11_demo")
        self.directory_sub_demo_01 = self.browse_ref("dms.directory_04_demo")
        self.directory_sub_demo_02 = self.browse_ref("dms.directory_12_demo")
        self.new_storage = self.create_storage(sudo=True)

    @multi_users(lambda self: self.multi_users(), callback="_setup_test_data")
    def test_create_directory(self):
        root_directory = self.create_directory(storage=self.new_storage)
        sub_directory = self.create_directory(directory=root_directory)
        self.assertEqual(sub_directory.storage_id.id, self.new_storage.id)
        self.assertEqual(root_directory.count_directories, 1)

    @multi_users(lambda self: self.multi_users(), callback="_setup_test_data")
    def test_copy_root_directory(self):
        copy_root_directory = self.directory_root_demo_03.copy()
        copy_root_directory.flush()
        self.assertEqual(
            self.directory_root_demo_03.storage_id.id, copy_root_directory.storage_id.id
        )
        self.assertEqual(
            self.directory_root_demo_03.count_directories,
            copy_root_directory.count_directories,
        )
        self.assertEqual(
            self.directory_root_demo_03.count_files, copy_root_directory.count_files
        )

    @multi_users(lambda self: self.multi_users(), callback="_setup_test_data")
    def test_copy_sub_directory(self):
        copy_sub_directory = self.directory_sub_demo_01.copy()
        self.assertEqual(
            self.directory_sub_demo_01.storage_id.id, copy_sub_directory.storage_id.id
        )
        self.assertEqual(
            self.directory_sub_demo_01.count_directories,
            copy_sub_directory.count_directories,
        )
        self.assertEqual(
            self.directory_sub_demo_01.count_files, copy_sub_directory.count_files
        )

    @multi_users(lambda self: self.multi_users(), callback="_setup_test_data")
    def test_rename_directory(self):
        path_names = self.directory_sub_demo_01.complete_name
        self.directory_root_demo_01.write({"name": "New Test Name"})
        self.assertNotEqual(path_names, self.directory_sub_demo_01.complete_name)

    @multi_users(lambda self: self.multi_users(), callback="_setup_test_data")
    def test_move_directory(self):
        path_names = self.directory_sub_demo_01.complete_name
        self.directory_root_demo_01.write(
            {
                "root_storage_id": False,
                "is_root_directory": False,
                "parent_id": self.directory_root_demo_02.id,
            }
        )
        self.assertNotEqual(path_names, self.directory_sub_demo_01.complete_name)

    @multi_users(lambda self: self.multi_users(), callback="_setup_test_data")
    def test_unlink_directory(self):
        root_directory = self.create_directory(storage=self.new_storage)
        sub_directory = self.create_directory(directory=root_directory)
        sub_files = self.create_file(directory=sub_directory)
        root_directory.unlink()
        self.assertFalse(sub_directory.exists())
        self.assertFalse(sub_files.exists())

    @multi_users(lambda self: self.multi_users(), callback="_setup_test_data")
    def test_storage(self):
        new_storage = self.create_storage(sudo=True)
        root_directory = self.create_directory(storage=self.new_storage)
        sub_directory = self.create_directory(directory=root_directory)
        self.assertEqual(sub_directory.storage_id.id, self.new_storage.id)
        root_directory.write({"root_storage_id": new_storage.id})
        self.assertEqual(sub_directory.storage_id.id, new_storage.id)

    @multi_users(lambda self: self.multi_users(), callback="_setup_test_data")
    def test_starred(self):
        self.directory_root_demo_01.toggle_starred()
        self.directory_root_demo_02.write({"starred": True})
        starred = self.directory.search([("starred", "=", True)])
        self.assertIn(self.directory_root_demo_01.id, starred.ids)
        self.assertIn(self.directory_root_demo_02.id, starred.ids)

    @multi_users(lambda self: self.multi_users(), callback="_setup_test_data")
    def test_count_directories(self):
        self.assertTrue(self.directory_root_demo_01.count_directories)

    @multi_users(lambda self: self.multi_users(), callback="_setup_test_data")
    def test_count_files(self):
        self.assertTrue(self.directory_sub_demo_01.count_files)

    @multi_users(lambda self: self.multi_users(), callback="_setup_test_data")
    def test_count_elements(self):
        self.assertTrue(self.directory_root_demo_01.count_elements)

    @multi_users(lambda self: self.multi_users(), callback="_setup_test_data")
    def test_count_total_directories(self):
        self.assertTrue(self.directory_root_demo_01.count_total_directories)

    @multi_users(lambda self: self.multi_users(), callback="_setup_test_data")
    def test_count_count_total_files(self):
        self.assertTrue(self.directory_root_demo_01.count_total_files)

    @multi_users(lambda self: self.multi_users(), callback="_setup_test_data")
    def test_count_total_elements(self):
        self.assertTrue(self.directory_root_demo_01.count_total_elements)

    @multi_users(lambda self: self.multi_users(), callback="_setup_test_data")
    def test_size(self):
        self.assertTrue(self.directory_root_demo_01.size)

    @multi_users(lambda self: self.multi_users(), callback="_setup_test_data")
    def test_name_get(self):
        directory = self.directory_sub_demo_01.with_context(
            dms_directory_show_path=True
        )
        self.assertTrue(
            "/" in directory.with_context(dms_directory_show_path=True).name_get()[0][1]
        )

    @multi_users(lambda self: self.multi_users(), callback="_setup_test_data")
    def test_name_search(self):
        directories = self.directory.name_search("/")
        self.assertTrue(len(directories))

    @multi_users(lambda self: self.multi_users(), callback="_setup_test_data")
    def test_search_panel(self):
        self.assertTrue(self.directory.search_panel_select_multi_range("parent_id"))
        self.assertTrue(self.directory.search_panel_select_multi_range("category_id"))
        self.assertTrue(self.directory.search_panel_select_multi_range("tag_ids"))
