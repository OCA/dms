from odoo.exceptions import AccessError, UserError
from odoo.tests.common import new_test_user, users
from odoo.tools.safe_eval import safe_eval

from odoo.addons.dms.tests.common import StorageDatabaseBaseCase


class DmsUiNativeWorkspaceTestCase(StorageDatabaseBaseCase):
    @users("dms-manager")
    def test_original_menu_visibility_uses_active_without_changing_groups(self):
        settings = self.env["res.config.settings"]
        menus = self.env.ref("dms.menu_dms_file") | self.env.ref(
            "dms.menu_dms_directory"
        )
        groups = {menu.id: menu.groups_id.ids for menu in menus}

        settings._dms_ui_set_menu_visibility(
            ["dms.menu_dms_file", "dms.menu_dms_directory"],
            False,
        )
        self.assertFalse(any(menus.mapped("active")))
        self.assertEqual({menu.id: menu.groups_id.ids for menu in menus}, groups)

        settings._dms_ui_set_menu_visibility(
            ["dms.menu_dms_file", "dms.menu_dms_directory"],
            True,
        )
        self.assertTrue(all(menus.mapped("active")))
        self.assertEqual({menu.id: menu.groups_id.ids for menu in menus}, groups)

    @users("dms-manager")
    def test_optional_dms_field_menu_visibility(self):
        menu = self.env.ref("dms_field.dms_storage_menu", raise_if_not_found=False)
        if not menu:
            self.skipTest("dms_field is not installed")
        groups = menu.groups_id
        self.env["res.config.settings"]._dms_ui_set_menu_visibility(
            ["dms_field.dms_storage_menu"],
            False,
        )
        self.assertFalse(menu.active)
        self.assertEqual(menu.groups_id, groups)

    @users("dms-manager")
    def test_documents_action_uses_native_workspace(self):
        workspace_view = self.env.ref(
            "dms_workspace_ui.view_dms_file_kanban_workspace_ui"
        )
        action = self.env["res.users"].dms_ui_action_documents()
        context = action["context"]
        if isinstance(context, str):
            context = safe_eval(context)
        self.assertTrue(context["dms_ui_workspace"])
        self.assertEqual(action["views"][0][0], workspace_view.id)

    def test_user_preferences_allow_cross_module_user_creation_defaults(self):
        user = new_test_user(self.env, login="workspace-default-user")
        self.assertEqual(user.dms_ui_custom_theme, "purple")

    @users("dms-manager")
    def test_bypass_delete_confirmation_setting_defaults_off_and_tracks_parameter(self):
        parameters = self.env["ir.config_parameter"].sudo()
        settings = self.env["res.config.settings"]
        parameters.set_param("dms_workspace_ui.bypass_delete_confirmation", "False")
        self.assertFalse(settings.dms_ui_bypass_delete_confirmation())

        parameters.set_param("dms_workspace_ui.bypass_delete_confirmation", "True")
        self.assertTrue(settings.dms_ui_bypass_delete_confirmation())

    @users("dms-manager")
    def test_archive_and_restore_directory_tree(self):
        child = self.create_directory(directory=self.directory)
        grandchild = self.create_directory(directory=child)
        nested_file = self.create_file(directory=grandchild)

        child.dms_ui_set_archived(True)
        self.assertFalse(child.active)
        self.assertFalse(grandchild.active)
        self.assertFalse(nested_file.active)

        child.with_context(active_test=False).dms_ui_set_archived(False)
        self.assertTrue(child.active)
        self.assertTrue(grandchild.active)
        self.assertTrue(nested_file.active)

    @users("dms-manager")
    def test_permanently_delete_archived_directory_tree(self):
        child = self.create_directory(directory=self.directory)
        nested_file = self.create_file(directory=child)

        child.dms_ui_set_archived(True)
        child.with_context(active_test=False).unlink()

        self.assertFalse(child.exists())
        self.assertFalse(nested_file.with_context(active_test=False).exists())

    @users("dms-manager")
    def test_archived_search_panel_contains_relevant_paths_and_direct_counts(self):
        child = self.create_directory(directory=self.directory)
        nested_file = self.create_file(directory=child)
        nested_file.action_archive()

        result = self.file_model.with_context(
            dms_ui_workspace=True
        ).search_panel_select_range(
            "directory_id",
            enable_counters=True,
            search_domain=[("active", "=", False)],
        )
        values = {value["id"]: value for value in result["values"]}
        self.assertIn(self.directory.id, values)
        self.assertIn(child.id, values)
        self.assertFalse(values[self.directory.id]["dms_ui_archived"])
        self.assertEqual(values[child.id]["__count"], 1)

    @users("dms-manager")
    def test_child_directory_payload_counts_only_active_children(self):
        child = self.create_directory(directory=self.directory)
        self.create_file(directory=child)
        archived_file = self.create_file(directory=child)
        self.create_directory(directory=child)
        archived_subfolder = self.create_directory(directory=child)

        archived_file.action_archive()
        archived_subfolder.dms_ui_set_archived(True)

        result = self.directory_model.dms_ui_child_directories(self.directory.id, [])
        payload = next(item for item in result if item["id"] == child.id)

        self.assertEqual(payload["fileCount"], 1)
        self.assertEqual(payload["folderCount"], 1)

    @users("dms-manager")
    def test_search_panel_refresh_data_contains_new_and_renamed_folder(self):
        child = self.create_directory(directory=self.directory)
        result = self.file_model.with_context(
            dms_ui_workspace=True
        ).search_panel_select_range("directory_id", search_domain=[])
        values = {value["id"]: value for value in result["values"]}
        self.assertIn(child.id, values)

        child.name = "Renamed folder"
        result = self.file_model.with_context(
            dms_ui_workspace=True
        ).search_panel_select_range("directory_id", search_domain=[])
        values = {value["id"]: value for value in result["values"]}
        self.assertEqual(values[child.id]["display_name"], "Renamed folder")

        child.unlink()
        result = self.file_model.with_context(
            dms_ui_workspace=True
        ).search_panel_select_range("directory_id", search_domain=[])
        values = {value["id"]: value for value in result["values"]}
        self.assertNotIn(child.id, values)

    @users("dms-manager")
    def test_search_panel_returns_direct_counts_for_multiple_folders(self):
        child = self.create_directory(directory=self.directory)
        self.create_file(directory=child)

        result = self.file_model.with_context(
            dms_ui_workspace=True
        ).search_panel_select_range("directory_id", search_domain=[])
        values = {value["id"]: value for value in result["values"]}
        self.assertEqual(values[self.directory.id]["__count"], 1)
        self.assertEqual(values[child.id]["__count"], 1)

    @users("dms-manager")
    def test_bulk_color_write_updates_every_selected_file(self):
        other_file = self.create_file(directory=self.directory)

        (self.file | other_file).write({"color": 8})

        self.assertEqual(self.file.color, 8)
        self.assertEqual(other_file.color, 8)

    @users("dms-manager")
    def test_cut_rejects_moving_directory_inside_itself(self):
        child = self.create_directory(directory=self.directory)
        grandchild = self.create_directory(directory=child)

        with self.assertRaises(UserError):
            self.directory_model.dms_ui_paste(
                grandchild.id,
                "cut",
                [{"type": "directory", "id": child.id}],
            )

    @users("dms-manager")
    def test_copy_directory_tree_uses_collision_safe_names(self):
        child = self.create_directory(directory=self.directory)
        grandchild = self.create_directory(directory=child)
        nested_file = self.create_file(directory=grandchild)

        result = self.directory_model.dms_ui_paste(
            self.directory.id,
            "copy",
            [{"type": "directory", "id": child.id}],
        )

        copies = self.directory_model.search(
            [("parent_id", "=", self.directory.id), ("id", "!=", child.id)]
        )
        self.assertEqual(len(copies), 1)
        self.assertEqual(result["mode"], "copy")
        self.assertEqual(result["target_directory_id"], self.directory.id)
        self.assertEqual(result["directories"][0]["id"], copies.id)
        self.assertNotEqual(copies.name, child.name)
        copied_grandchild = copies.child_directory_ids
        self.assertEqual(len(copied_grandchild), 1)
        self.assertEqual(len(copied_grandchild.file_ids), 1)
        self.assertNotEqual(copied_grandchild.file_ids.name, nested_file.name)

    @users("dms-manager")
    def test_copy_file_to_another_directory(self):
        destination = self.create_directory(directory=self.directory)

        result = self.directory_model.dms_ui_paste(
            destination.id,
            "copy",
            [{"type": "file", "id": self.file.id}],
        )

        copied_files = self.file_model.search([("directory_id", "=", destination.id)])
        self.assertEqual(len(copied_files), 1)
        self.assertEqual(copied_files.name, self.file.name)
        self.assertEqual(result["files"][0]["id"], copied_files.id)

    @users("dms-manager")
    def test_cut_returns_moved_records_for_focus_restoration(self):
        destination = self.create_directory(directory=self.directory)

        result = self.directory_model.dms_ui_paste(
            destination.id,
            "cut",
            [{"type": "file", "id": self.file.id}],
        )

        self.assertEqual(result["mode"], "cut")
        self.assertEqual(result["target_directory_id"], destination.id)
        self.assertEqual(result["files"][0]["id"], self.file.id)
        self.assertEqual(self.file.directory_id, destination)

    @users("dms-manager")
    def test_create_root_folder_from_all_files(self):
        root = self.directory_model.browse(
            self.directory_model.dms_ui_create_folder(False, "New root")
        )
        self.assertTrue(root.is_root_directory)
        self.assertTrue(root.storage_id)
        self.assertTrue(root.group_ids)

    @users("basic-user")
    def test_clipboard_and_archive_require_dms_permissions(self):
        directory = self.directory.with_user(self.env.user)
        directory_model = self.directory_model.with_user(self.env.user)
        with self.assertRaises(AccessError):
            directory.dms_ui_set_archived(True)
        with self.assertRaises(AccessError):
            directory_model.dms_ui_paste(
                directory.id,
                "copy",
                [{"type": "file", "id": self.file.id}],
            )
