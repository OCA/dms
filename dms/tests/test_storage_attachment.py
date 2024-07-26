# Copyright 2021-2022 Tecnativa - Víctor Martínez
# Copyright 2021 Tecnativa - João Marques
# Copyright 2024 Subteno - Timothée Vannier (https://www.subteno.com).
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.tests.common import users
from odoo.tools import mute_logger

from .common import StorageAttachmentBaseCase


class StorageAttachmentTestCase(StorageAttachmentBaseCase):
    @users("dms-manager")
    @mute_logger("odoo.models.unlink")
    def test_storage_attachment(self):
        self._create_attachment("demo.txt")
        self.assertTrue(
            self.storage.storage_file_ids.filtered(lambda x: x.name == "demo.txt"),
            "File should be created",
        )
        directory = self._get_partner_directory()
        self.assertEqual(directory.count_files, 1, "Directory should have 1 file")
        self.assertEqual(
            directory.file_ids[0].name, "demo.txt", "File should be demo.txt"
        )
        file_01 = self.create_file(directory=directory)
        self.assertEqual(file_01.storage_id, self.storage, "Storage should be the same")
        self.assertEqual(
            file_01.storage_id.save_type, "attachment", "Save type should be attachment"
        )
        self.assertEqual(file_01.save_type, "database", "Save type should be database")
        self.assertEqual(directory.count_files, 2, "Directory should have 2 files")
        # Assert cascade removal
        self.partner.unlink()
        self.assertFalse(file_01.exists(), "File should not exist")
        self.assertFalse(directory.exists(), "Directory should not exist")

    @users("dms-manager")
    def test_storage_attachment_misc(self):
        attachment = self._create_attachment("demo.txt")
        root_directory = self.storage.root_directory_ids.filtered(
            lambda x: x.is_root_directory
        )
        self.assertEqual(
            root_directory.count_directories,
            1,
            "Root directory should have 1 directory",
        )
        self.assertEqual(
            len(root_directory.child_directory_ids),
            1,
            "Root directory should have 1 child directory",
        )
        child_directory = root_directory.child_directory_ids[0]
        self.assertEqual(
            child_directory.res_model,
            self.partner_model._name,
            "Model should be res.partner",
        )
        self.assertEqual(
            child_directory.res_id, self.partner.id, "Record ID should be partner ID"
        )
        self.assertEqual(
            len(root_directory.child_directory_ids.file_ids),
            1,
            "Root directory should have 1 file",
        )
        dms_file = root_directory.child_directory_ids.file_ids[0]
        self.assertEqual(
            dms_file.attachment_id, attachment, "Attachment should be the same"
        )
        self.assertEqual(dms_file.name, "demo.txt", "Name should be demo.txt")
        self.assertEqual(
            dms_file.res_model, self.partner_model._name, "Model should be res.partner"
        )
        self.assertEqual(
            dms_file.res_id, self.partner.id, "Record ID should be partner ID"
        )
        directory = self._get_partner_directory()
        file_01 = self.create_file(directory=directory)
        self.assertEqual(
            file_01.res_model, self.partner_model._name, "Model should be res.partner"
        )
        self.assertEqual(
            file_01.res_id, self.partner.id, "Record ID should be partner ID"
        )
        self.assertEqual(file_01.storage_id, self.storage, "Storage should be the same")
        self.assertEqual(
            file_01.storage_id.save_type, "attachment", "Save type should be attachment"
        )
        self.assertEqual(file_01.save_type, "database", "Save type should be database")
        self.assertEqual(
            self.storage.count_storage_files, 2, "Storage should have 2 files"
        )

    @users("dms-manager")
    def test_storage_attachment_directory_record_ref_access_dms_manager(self):
        self._create_attachment("demo.txt")
        directory = self._get_partner_directory()
        self.assertTrue(directory.permission_read, "Permission read should be True")
        self.assertEqual(self.partner.type, "contact", "Type should be contact")
        self.assertTrue(
            directory.sudo().permission_read, "Permission read should be True"
        )

    @users("dms-user")
    def test_storage_attachment_directory_record_ref_access_dms_user(self):
        self._create_attachment("demo.txt")
        directory = self._get_partner_directory()
        self.assertTrue(directory.permission_read, "Permission read should be True")
        self.assertEqual(self.partner.type, "contact", "Type should be contact")
        self.assertTrue(
            directory.sudo().permission_read, "Permission read should be True"
        )
        directory.invalidate_recordset()
        self.assertTrue(
            directory.permission_read, "Permission read should still be True"
        )

    @users("basic-user")
    def test_storage_attachment_directory_record_ref_access_basic_user(self):
        self._create_attachment("demo.txt")
        directory = self._get_partner_directory()
        self.assertTrue(directory.permission_read, "Permission read should be True")
        self.assertTrue(directory.permission_read, "Permission read should be True")
        self.assertEqual(self.partner.type, "contact", "Type should be contact")
        self.partner.sudo().write({"type": "other"})
        self.assertEqual(self.partner.type, "other", "Type should now be other")
        self.assertTrue(
            directory.sudo().permission_read, "Permission read should be True"
        )

    @users("basic-user")
    def test_create_attachment_basic_user(self):
        attachment = self._create_attachment("Test file")
        self.assertEqual(attachment.name, "Test file", "Name should be Test file")
        self.assertTrue(self._get_partner_directory(), "Directory should exist")
