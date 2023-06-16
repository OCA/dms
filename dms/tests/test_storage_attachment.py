# Copyright 2021-2022 Tecnativa - Víctor Martínez
# Copyright 2021 Tecnativa - João Marques
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.tests.common import users

from .common import StorageAttachmentBaseCase


class StorageAttachmentTestCase(StorageAttachmentBaseCase):
    @users("dms-manager")
    def test_storage_attachment(self):
        self._create_attachment("demo.txt")
        self.assertTrue(
            self.storage.storage_file_ids.filtered(lambda x: x.name == "demo.txt")
        )
        directory = self._get_partner_directory()
        self.assertEqual(directory.count_files, 1)
        self.assertEqual(directory.file_ids[0].name, "demo.txt")
        file_01 = self.create_file(directory=directory)
        self.assertEqual(file_01.storage_id, self.storage)
        self.assertEqual(file_01.storage_id.save_type, "attachment")
        self.assertEqual(file_01.save_type, "database")
        self.assertEqual(directory.count_files, 2)
        # Assert cascade removal
        self.partner.unlink()
        self.assertFalse(file_01.exists())
        self.assertFalse(directory.exists())

    @users("dms-manager")
    def test_storage_attachment_misc(self):
        attachment = self._create_attachment("demo.txt")
        root_directory = self.storage.root_directory_ids.filtered(
            lambda x: x.is_root_directory
        )
        self.assertEqual(root_directory.count_directories, 1)
        self.assertEqual(len(root_directory.child_directory_ids), 1)
        child_directory = root_directory.child_directory_ids[0]
        self.assertEqual(child_directory.res_model, self.partner_model._name)
        self.assertEqual(child_directory.res_id, self.partner.id)
        self.assertEqual(len(root_directory.child_directory_ids.file_ids), 1)
        dms_file = root_directory.child_directory_ids.file_ids[0]
        self.assertEqual(dms_file.attachment_id, attachment)
        self.assertEqual(dms_file.name, "demo.txt")
        self.assertEqual(dms_file.res_model, self.partner_model._name)
        self.assertEqual(dms_file.res_id, self.partner.id)
        directory = self._get_partner_directory()
        file_01 = self.create_file(directory=directory)
        self.assertEqual(file_01.res_model, self.partner_model._name)
        self.assertEqual(file_01.res_id, self.partner.id)
        self.assertEqual(file_01.storage_id, self.storage)
        self.assertEqual(file_01.storage_id.save_type, "attachment")
        self.assertEqual(file_01.save_type, "database")
        self.assertEqual(self.storage.count_storage_files, 2)

    @users("dms-manager")
    def test_storage_attachment_directory_record_ref_access_dms_manager(self):
        self._create_attachment("demo.txt")
        directory = self._get_partner_directory()
        self.assertTrue(directory.permission_read)
        self.assertEqual(self.partner.type, "contact")
        self.partner.sudo().write({"type": "private"})
        self.assertEqual(self.partner.type, "private")
        self.assertTrue(directory.sudo().permission_read)
        directory.invalidate_cache()
        self.assertFalse(directory.with_user(self.dms_manager_user).permission_read)

    @users("dms-user")
    def test_storage_attachment_directory_record_ref_access_dms_user(self):
        self._create_attachment("demo.txt")
        directory = self._get_partner_directory()
        self.assertTrue(directory.permission_read)
        self.assertEqual(self.partner.type, "contact")
        self.partner.sudo().write({"type": "private"})
        self.assertEqual(self.partner.type, "private")
        self.assertTrue(directory.sudo().permission_read)
        directory.invalidate_cache()
        self.assertFalse(directory.with_user(self.dms_user).permission_read)
        # user can access self.partner
        self.dms_user.write(
            {
                "groups_id": [
                    (
                        6,
                        0,
                        [
                            self.browse_ref("base.group_private_addresses").id,
                            self.browse_ref("base.group_user").id,
                        ],
                    )
                ]
            }
        )
        self.assertTrue(directory.permission_read)

    @users("basic-user")
    def test_storage_attachment_directory_record_ref_access_basic_user(self):
        self._create_attachment("demo.txt")
        directory = self._get_partner_directory()
        self.assertTrue(directory.permission_read)
        self.assertTrue(directory.permission_read)
        self.assertEqual(self.partner.type, "contact")
        self.partner.sudo().write({"type": "private"})
        self.assertEqual(self.partner.type, "private")
        self.assertTrue(directory.sudo().permission_read)
        directory.invalidate_cache()
        self.assertFalse(directory.with_user(self.user).permission_read)

    @users("basic-user")
    def test_create_attachment_basic_user(self):
        attachment = self._create_attachment("Test file")
        self.assertEqual(attachment.name, "Test file")
        self.assertTrue(self._get_partner_directory())
