# Copyright 2021 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from .common import DocumentsBaseCase


class StorageAttachmentTestCase(DocumentsBaseCase):
    def setUp(self):
        super().setUp()
        self.storage = self.browse_ref("dms.storage_attachment_demo")
        self.model_res_partner = self.browse_ref("base.model_res_partner")
        self.partner = self.env["res.partner"].create({"name": "test partner"})

    def _create_attachment(self, name, uid):
        self.create_attachment(
            name=name,
            res_model=self.model_res_partner.model,
            res_id=self.partner.id,
            sudo=False,
        ).sudo(uid)

    def test_storage_attachment(self):
        self._create_attachment("demo.txt", self.admin_uid)
        self.assertEqual(self.storage.count_storage_files, 1)
        directory_id = self.directory.sudo(self.admin_uid).search(
            [
                ("storage_id", "=", self.storage.id),
                ("res_model", "=", self.model_res_partner.model),
                ("res_id", "=", self.partner.id),
            ]
        )
        self.assertEqual(directory_id.count_files, 1)
        self.assertEqual(directory_id.file_ids[0].name, "demo.txt")
        file_01 = self.create_file_with_context(
            context={"default_res_model": self.model_res_partner.model},
            directory=directory_id,
            storage=directory_id.storage_id,
        ).sudo(self.admin_uid)
        self.assertEqual(file_01.storage_id, self.storage)
        self.assertEqual(file_01.storage_id.save_type, "attachment")
        self.assertEqual(file_01.save_type, "database")
        self.assertEqual(self.storage.count_storage_files, 2)
        # Assert cascade removal
        self.partner.unlink()
        self.assertFalse(file_01.exists())
        self.assertFalse(directory_id.exists())

    def test_storage_attachment_directory_record_ref_access(self):
        self._create_attachment("demo.txt", self.admin_uid)
        directory_id = self.directory.sudo(self.admin_uid).search(
            [
                ("storage_id", "=", self.storage.id),
                ("res_model", "=", self.model_res_partner.model),
                ("res_id", "=", self.partner.id),
            ]
        )
        self.assertTrue(directory_id.sudo(self.admin_uid).check_access("read"))
        # demo can access res_partner_12
        self.browse_ref("base.user_demo").write(
            {"groups_id": [(2, self.browse_ref("dms.group_dms_user").id, False)]}
        )
        self.assertEqual(self.partner.type, "contact")
        self.assertTrue(directory_id.sudo(self.demo_uid).check_access("read"))
        self.partner.sudo().write({"type": "private"})
        self.assertEqual(self.partner.type, "private")
        self.assertFalse(directory_id.sudo(self.demo_uid).check_access("read"))
