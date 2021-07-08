# Copyright 2021 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from .common import DocumentsBaseCase


class StorageAttachmentTestCase(DocumentsBaseCase):
    def setUp(self):
        super().setUp()
        self.storage = self.browse_ref("dms.storage_attachment_demo")
        self.model_res_partner = self.browse_ref("base.model_res_partner")
        self.partner = self.env["res.partner"].create({"name": "test partner"})
        self.user = self.env["res.users"].create(
            {
                "name": "name",
                "login": "login",
                "groups_id": [(6, 0, [self.env.ref("base.group_user").id])],
            }
        )

    def _create_attachment(self, name, uid):
        self.create_attachment(
            name=name,
            res_model=self.model_res_partner.model,
            res_id=self.partner.id,
            sudo=False,
        ).with_user(uid)

    def test_storage_attachment(self):
        self._create_attachment("demo.txt", self.admin_uid)
        self.assertTrue(
            self.storage.storage_file_ids.filtered(lambda x: x.name == "demo.txt")
        )
        directory_id = self.directory.with_user(self.admin_uid).search(
            [
                ("storage_id", "=", self.storage.id),
                ("res_model", "=", self.model_res_partner.model),
                ("res_id", "=", self.partner.id),
            ]
        )
        self.assertEqual(directory_id.count_files, 1)
        self.assertEqual(directory_id.file_ids[0].name, "demo.txt")
        file_01 = self.create_file(
            directory=directory_id, storage=directory_id.storage_id,
        ).with_user(self.admin_uid)
        self.assertEqual(file_01.storage_id, self.storage)
        self.assertEqual(file_01.storage_id.save_type, "attachment")
        self.assertEqual(file_01.save_type, "database")
        self.assertEqual(directory_id.count_files, 2)
        # Assert cascade removal
        self.partner.unlink()
        self.assertFalse(file_01.exists())
        self.assertFalse(directory_id.exists())

    def test_storage_attachment_directory_record_ref_access(self):
        self._create_attachment("demo.txt", self.admin_uid)
        directory_id = self.directory.with_user(self.admin_uid).search(
            [
                ("storage_id", "=", self.storage.id),
                ("res_model", "=", self.model_res_partner.model),
                ("res_id", "=", self.partner.id),
            ]
        )
        self.assertTrue(directory_id.with_user(self.admin_uid).permission_read)
        self.assertTrue(directory_id.with_user(self.demo_uid).permission_read)
        self.assertTrue(directory_id.with_user(self.user.id).permission_read)
        self.assertEqual(self.partner.type, "contact")
        self.partner.sudo().write({"type": "private"})
        self.assertEqual(self.partner.type, "private")
        self.assertTrue(directory_id.sudo().permission_read)
        if not self.browse_ref("base.user_admin").user_has_groups(
            "base.group_private_addresses"
        ):
            directory_id.with_user(self.admin_uid).invalidate_cache()
            self.assertFalse(directory_id.with_user(self.admin_uid).permission_read)
        if not self.browse_ref("base.user_demo").user_has_groups(
            "base.group_private_addresses"
        ):
            directory_id.with_user(self.demo_uid).invalidate_cache()
            self.assertFalse(directory_id.with_user(self.demo_uid).permission_read)
        directory_id.with_user(self.user).invalidate_cache()
        self.assertFalse(directory_id.with_user(self.user.id).permission_read)
        # user can access self.partner
        self.browse_ref("base.user_demo").write(
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
        self.assertTrue(directory_id.with_user(self.demo_uid).permission_read)
