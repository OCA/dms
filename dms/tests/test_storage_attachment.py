# Copyright 2021 Tecnativa - Víctor Martínez
# Copyright 2021 Tecnativa - João Marques
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
        self.user_demo = self.env["res.users"].create(
            {
                "name": "User Base",
                "login": "user_demo",
                "groups_id": [
                    (
                        6,
                        0,
                        [
                            self.env.ref("base.group_partner_manager").id,
                            self.env.ref("base.group_user").id,
                            self.env.ref("base.group_no_one").id,
                            self.env.ref("dms.group_dms_user").id,
                        ],
                    )
                ],
            }
        )
        self.user_admin = self.env["res.users"].create(
            {
                "name": "User Admin",
                "login": "user_admin",
                "groups_id": [
                    (
                        6,
                        0,
                        [
                            self.env.ref("base.group_erp_manager").id,
                            self.env.ref("base.group_partner_manager").id,
                            self.env.ref("base.group_user").id,
                            self.env.ref("dms.group_dms_manager").id,
                            self.env.ref("base.group_system").id,
                            self.env.ref("base.group_no_one").id,
                            self.env.ref("dms.group_dms_user").id,
                        ],
                    )
                ],
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
        self._create_attachment("demo.txt", self.user_admin.id)
        self.assertTrue(
            self.storage.storage_file_ids.filtered(lambda x: x.name == "demo.txt")
        )
        directory_id = self.directory.with_user(self.user_admin.id).search(
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
        ).with_user(self.user_admin.id)
        self.assertEqual(file_01.storage_id, self.storage)
        self.assertEqual(file_01.storage_id.save_type, "attachment")
        self.assertEqual(file_01.save_type, "database")
        self.assertEqual(directory_id.count_files, 2)
        # Assert cascade removal
        self.partner.unlink()
        self.assertFalse(file_01.exists())
        self.assertFalse(directory_id.exists())

    def test_storage_attachment_directory_record_ref_access(self):
        self._create_attachment("demo.txt", self.user_admin.id)
        directory_id = self.directory.with_user(self.user_admin.id).search(
            [
                ("storage_id", "=", self.storage.id),
                ("res_model", "=", self.model_res_partner.model),
                ("res_id", "=", self.partner.id),
            ]
        )
        self.assertTrue(directory_id.with_user(self.user_admin.id).permission_read)
        self.assertTrue(directory_id.with_user(self.user_demo.id).permission_read)
        self.assertTrue(directory_id.with_user(self.user.id).permission_read)
        self.assertEqual(self.partner.type, "contact")
        self.partner.sudo().write({"type": "private"})
        self.assertEqual(self.partner.type, "private")
        self.assertTrue(directory_id.sudo().permission_read)
        directory_id.invalidate_cache()
        self.assertFalse(directory_id.with_user(self.user_admin.id).permission_read)
        directory_id.invalidate_cache()
        self.assertFalse(directory_id.with_user(self.user_demo.id).permission_read)
        self.assertFalse(directory_id.with_user(self.user.id).permission_read)
        # user can access self.partner
        self.user_demo.write(
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
        self.assertTrue(directory_id.with_user(self.user_demo.id).permission_read)
