# Copyright 2024 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.tests import new_test_user
from odoo.tools import mute_logger

from odoo.addons.base.tests.common import BaseCommon


class TestHrDmsField(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, test_dms_field=True))
        cls.template = cls.env.ref("hr_dms_field.field_template_employee")
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
        read_access_hr_employee_group = self.env.ref(
            "hr_dms_field.read_access_hr_employee_group"
        )
        read_access_hr_employee_group.write(
            {
                "group_ids": [(5, 0)],
                "explicit_user_ids": [(6, 0, self.env.ref("base.user_admin").ids)],
            }
        )
        employee = self.employee_model.create({"name": "Test employee"})
        employee.invalidate_recordset()
        directory = employee.dms_directory_ids
        self.assertEqual(len(directory), 1)
        directory_0 = employee.dms_directory_ids[0]
        group_custom = directory_0.group_ids.filtered("dms_field_ref")
        self.assertFalse(group_custom.explicit_user_ids)
        # Use the demo user to modify the employee and link the user, it does not
        # have access to the directory.
        demo = self.env.ref("base.user_demo")
        employee = employee.with_user(demo)
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
