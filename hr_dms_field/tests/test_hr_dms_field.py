# Copyright 2024 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.tests import common, new_test_user


class TestHrDmsField(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(
                cls.env.context,
                mail_create_nolog=True,
                mail_create_nosubscribe=True,
                mail_notrack=True,
                no_reset_password=True,
                tracking_disable=True,
            )
        )
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
        employee.refresh()
        directory = employee.dms_directory_ids
        self.assertEqual(len(directory), 1)
        self.assertEqual(directory.storage_id, self.storage)
        self.assertIn("Autogenerate group", directory.group_ids.name)
        self.assertNotIn(self.access_group, directory.group_ids)
        self.assertNotIn(self.user, directory.group_ids.explicit_user_ids)
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
        employee.refresh()
        self.assertIn(self.user, employee.dms_directory_ids.group_ids.explicit_user_ids)
