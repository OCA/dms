# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import new_test_user
from odoo.tools import mute_logger

from odoo.addons.base.tests.common import BaseCommon


class TestDmsUserRole(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_a = new_test_user(cls.env, login="test_user_a")
        cls.user_b = new_test_user(cls.env, login="test_user_b")
        cls.user_c = new_test_user(cls.env, login="test_user_c")
        cls.access_group = cls.env["dms.access.group"].create(
            {"name": "Test group", "explicit_user_ids": [(4, cls.user_a.id)]}
        )
        cls.user_role = cls.env["res.users.role"].create({"name": "Test user role"})

    @mute_logger("odoo.models.unlink")
    def test_user_role_change(self):
        self.assertIn(self.user_a, self.access_group.users)
        self.assertNotIn(self.user_b, self.access_group.users)
        self.assertNotIn(self.user_c, self.access_group.users)
        # Add User a to user_role: Without changes
        self.user_role.line_ids = [(0, 0, {"user_id": self.user_a.id})]
        self.assertIn(self.user_a, self.access_group.users)
        self.assertNotIn(self.user_b, self.access_group.users)
        self.assertNotIn(self.user_c, self.access_group.users)
        # Set role to access group: Without changes
        self.access_group.role_ids = [(4, self.user_role.id)]
        self.assertIn(self.user_a, self.access_group.users)
        self.assertNotIn(self.user_b, self.access_group.users)
        self.assertNotIn(self.user_c, self.access_group.users)
        # Add User b to user_role: User b is added to access groups
        self.user_role.line_ids = [(0, 0, {"user_id": self.user_b.id})]
        self.assertIn(self.user_a, self.access_group.users)
        self.assertIn(self.user_b, self.access_group.users)
        self.assertNotIn(self.user_c, self.access_group.users)
        # Add User c to user_role: User c is added to access groups
        self.user_role.line_ids = [(0, 0, {"user_id": self.user_c.id})]
        self.assertIn(self.user_a, self.access_group.users)
        self.assertIn(self.user_b, self.access_group.users)
        self.assertIn(self.user_c, self.access_group.users)
        # Remove User c from user role: User c is removed from access group
        line_b = self.user_role.line_ids.filtered(lambda x: x.user_id == self.user_b)
        self.user_role.line_ids = [(3, line_b.id)]
        self.assertIn(self.user_a, self.access_group.users)
        self.assertNotIn(self.user_b, self.access_group.users)
        self.assertIn(self.user_c, self.access_group.users)
