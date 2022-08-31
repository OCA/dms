from odoo.tests import SavepointCase

from .common import multi_users


class AccessGroupTestCase(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.DmsAccessGroup = cls.env["dms.access.group"]
        cls.base_user = cls.env["res.users"].create(
            {
                "name": "Base User",
                "login": "base",
                "groups_id": [(6, 0, [cls.env.ref("base.group_user").id])],
            }
        )
        cls.dms_user = cls.env["res.users"].create(
            {
                "name": "DMS User",
                "login": "dms_user",
                "groups_id": [(6, 0, [cls.env.ref("dms.group_dms_user").id])],
            }
        )
        cls.dms_manager = cls.env["res.users"].create(
            {
                "name": "DMS Manager",
                "login": "dms_manager",
                "groups_id": [(6, 0, [cls.env.ref("dms.group_dms_manager").id])],
            }
        )

        cls.access_group_base_user = cls.DmsAccessGroup.create(
            {"name": "Base Group", "create_uid": cls.base_user.id}
        )
        cls.access_group_dms_user = cls.DmsAccessGroup.create(
            {"name": "DMS User Group", "create_uid": cls.dms_user.id}
        )
        cls.access_group_dms_manager = cls.DmsAccessGroup.create(
            {"name": "DMS Manager Group", "create_uid": cls.dms_manager.id}
        )
        cls.test_access_groups = (
            cls.access_group_base_user
            + cls.access_group_dms_user
            + cls.access_group_dms_manager
        )

    @multi_users(
        lambda self: (
            (self.base_user.id, True),
            (self.dms_user.id, True),
            (self.dms_manager.id, True),
        ),
    )
    def test_can_read_all_groups(self):
        access_groups = (
            self.env["dms.access.group"]
            .sudo(self.uid)
            .search([("id", "in", self.test_access_groups.ids)])
        )
        self.assertEqual(len(self.test_access_groups), len(access_groups))

    @multi_users(
        lambda self: (
            (self.base_user.id, False),
            (self.dms_user.id, True),
            (self.dms_manager.id, True),
        ),
    )
    def test_can_create_groups(self):
        self.DmsAccessGroup.sudo(self.uid).create({"name": "test"})

    @multi_users(
        lambda self: (
            (self.base_user.id, False),
            (self.dms_user.id, True),
            (self.dms_manager.id, True),
        ),
    )
    def test_write_unlink_own_group(self):
        access_group = self.test_access_groups.filtered(
            lambda x: x.create_uid.id == self.uid
        )
        access_group.sudo(self.uid).write({"name": "New name"})
        access_group.sudo(self.uid).unlink()

    @multi_users(
        lambda self: (
            (self.base_user.id, False),
            (self.dms_user.id, False),
            (self.dms_manager.id, True),
        ),
    )
    def write_unlink_other_group(self):
        access_groups = self.test_access_groups.filtered(
            lambda x: x.create_uid.id != self.uid
        )
        for group in access_groups:
            group.sudo(self.uid).write({"name": "New name"})
            group.sudo(self.uid).unlink()
