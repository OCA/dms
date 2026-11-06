# Copyright 2026 NovoAuxilia
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo.tests import new_test_user

from .common import DocumentsBaseCase


class TestAccessGroupImpliedUsers(DocumentsBaseCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.dms_users_group = cls.access_group_model.create(
            {
                "name": "All DMS users",
                "group_ids": [(6, 0, [cls.env.ref("dms.group_dms_user").id])],
            }
        )

    def test_users_implying_the_group_are_members(self):
        """DMS managers get the DMS user group through implied groups only."""
        self.assertIn(self.dms_user, self.dms_users_group.users)
        self.assertIn(self.dms_manager_user, self.dms_users_group.users)

    def test_user_given_an_implying_group_later_becomes_member(self):
        user = new_test_user(self.env, login="dms-late-manager")
        self.assertNotIn(user, self.dms_users_group.users)
        user.write({"group_ids": [(4, self.env.ref("dms.group_dms_manager").id)]})
        self.assertIn(user, self.dms_users_group.users)

    def test_manager_reads_directory_shared_with_dms_users(self):
        directory = self.directory_model.create(
            {
                "name": "Shared with DMS users",
                "is_root_directory": True,
                "storage_id": self.create_storage().id,
                "group_ids": [(6, 0, [self.dms_users_group.id])],
            }
        )
        self.assertTrue(directory.with_user(self.dms_manager_user).permission_read)
        self.assertTrue(directory.with_user(self.dms_user).permission_read)
