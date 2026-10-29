# Copyright 2024-2025 Tecnativa - Víctor Martínez
# Copyright 2026 Tecnativa - Carlos Roca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import Command
from odoo.tests import new_test_user
from odoo.tools import mute_logger

from odoo.addons.base.tests.common import BaseCommon

from .common import HrDmsFieldTestMixin


class TestHrDmsField(HrDmsFieldTestMixin, BaseCommon):
    # Keep running the tests as superuser, tests switch users explicitly
    _test_user_groups = ()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, test_dms_field=True))
        cls.template = cls._create_employee_template()
        cls.storage = cls.template.storage_id
        cls.access_group = cls.template.group_ids
        cls.env["dms.directory"].create(
            {
                "name": "Payrolls",
                "parent_id": cls.template.dms_directory_ids[0].id,
                "storage_id": cls.template.storage_id.id,
            }
        )
        cls.env["dms.directory"].create(
            {
                "name": "Contracts",
                "parent_id": cls.template.dms_directory_ids[0].id,
                "storage_id": cls.template.storage_id.id,
            }
        )
        cls.user = new_test_user(cls.env, login="test-user")
        cls.employee_model = cls.env["hr.employee"]

    def test_employee_exists(self):
        employee = self.employee_model.search([], limit=1)
        self.assertEqual(len(employee.dms_directory_ids), 0)

    def test_employee_create_01(self):
        employee = self.employee_model.create({"name": "Test employee"})
        # Manually refresh, similar to UX
        # dms_field/static/src/views/dms_list/dms_list_renderer.esm.js#L450
        employee.invalidate_model()
        directory = employee.dms_directory_ids
        self.assertEqual(len(directory), 1)
        self.assertEqual(directory.storage_id, self.storage)
        group_custom = directory.group_ids.filtered("dms_field_ref")
        self.assertIn(self.access_group, directory.group_ids)
        self.assertNotIn(self.user, group_custom.explicit_user_ids)
        child_directory_names = directory.mapped("child_directory_ids.name")
        self.assertIn("Payrolls", child_directory_names)
        self.assertIn("Contracts", child_directory_names)

    def test_employee_create_02(self):
        employee = self.employee_model.create(
            {
                "name": "Test employee",
                "user_id": self.user.id,
            }
        )
        # Manually refresh, similar to UX
        # dms_field/static/src/views/dms_list/dms_list_renderer.esm.js#L450
        employee.invalidate_model()
        group_custom = employee.dms_directory_ids.group_ids.filtered("dms_field_ref")
        self.assertIn(self.user, group_custom.explicit_user_ids)

    def test_employee_write_custom(self):
        self.access_group.write(
            {
                "group_ids": [Command.set([])],
                "explicit_user_ids": [Command.set(self.env.ref("base.user_admin").ids)],
            }
        )
        employee = self.employee_model.create({"name": "Test employee"})
        employee.invalidate_recordset()
        directory = employee.dms_directory_ids
        self.assertEqual(len(directory), 1)
        directory_0 = employee.dms_directory_ids[0]
        group_custom = directory_0.group_ids.filtered("dms_field_ref")
        self.assertFalse(group_custom.explicit_user_ids)
        # Use an HR officer to modify the employee and link the user, it does not
        # have access to the directory.
        hr_user = new_test_user(
            self.env, login="test-hr-user", groups="base.group_user,hr.group_hr_user"
        )
        employee = employee.with_user(hr_user)
        employee.invalidate_recordset()
        employee.write({"user_id": self.user.id})
        self.assertIn(self.user, group_custom.explicit_user_ids)

    @mute_logger("odoo.models.unlink")
    def test_employee_full_process(self):
        employee = self.employee_model.create(
            {
                "name": "Test employee",
                "user_id": self.user.id,
            }
        )
        # Manually refresh, similar to UX
        # dms_field/static/src/views/dms_list/dms_list_renderer.esm.js#L450
        employee.invalidate_model()
        directory_0 = employee.dms_directory_ids[0]
        group_custom = directory_0.group_ids.filtered("dms_field_ref")
        self.assertIn(self.user, group_custom.explicit_user_ids)
        employee.write({"user_id": False})
        self.assertFalse(group_custom.explicit_user_ids)
        employee.write({"user_id": self.user.id})
        self.assertIn(self.user, group_custom.explicit_user_ids)
        employee.unlink()
        self.assertFalse(directory_0.exists())
        self.assertFalse(group_custom.exists())

    def test_employee_form_view_with_dms_list(self):
        """The employee form views embedding a dms_list field can be generated."""
        for model in ("hr.employee", "hr.employee.public"):
            views = self.env[model].get_views([(False, "form")])
            arch = views["views"]["form"]["arch"]
            self.assertIn('mode="dms_list"', arch)
            self.assertIn("<dms_list", arch)

    def test_employee_public_is_logged(self):
        employee = self.employee_model.create(
            {"name": "Test employee", "user_id": self.user.id}
        )
        public_model = self.env["hr.employee.public"]
        self.assertTrue(public_model.with_user(self.user).browse(employee.id).is_logged)
        self.assertFalse(public_model.browse(employee.id).is_logged)
