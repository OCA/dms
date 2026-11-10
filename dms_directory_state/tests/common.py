# Copyright 2026 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.dms.tests.common import StorageDatabaseBaseCase


class Common(StorageDatabaseBaseCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.demo_user = cls.env.ref("base.user_demo")
        cls.no_change_access_group, cls.change_access_group = cls.env[
            "dms.access.group"
        ].create(
            [
                {
                    "name": "Test no change access Group",
                    "perm_change_state": False,  # Default
                    "perm_write": True,
                    "explicit_user_ids": cls.demo_user,
                },
                {
                    "name": "Test can change access Group",
                    "perm_change_state": True,
                    "perm_write": True,
                    "explicit_user_ids": cls.demo_user,
                },
            ]
        )
