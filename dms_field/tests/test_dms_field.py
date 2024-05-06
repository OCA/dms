# Copyright 2020 Creu Blanca
# Copyright 2024 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, new_test_user


class TestDmsField(TransactionCase):
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
        cls.user_a = new_test_user(cls.env, login="test-user-a")
        cls.group = cls.env["res.groups"].create(
            {"name": "Test group", "users": [(4, cls.user_a.id)]}
        )
        cls.user_b = new_test_user(cls.env, login="test-user-b")
        cls.template = cls.env["dms.field.template"].create(
            {
                "name": "Partner",
                "storage_id": cls.env.ref("dms.storage_demo").id,
                "model_id": cls.env.ref("base.model_res_partner").id,
                "group_ids": [(4, cls.env.ref("dms.access_group_01_demo").id)],
                "directory_format_name": "{{object.display_name}}",
            }
        )
        cls.template.group_ids.group_ids = [(4, cls.group.id)]
        cls.template.group_ids.explicit_user_ids = [(4, cls.user_b.id)]
        cls.storage = cls.template.storage_id
        template_ctx = cls.template.with_context(
            res_model=cls.template._name, res_id=cls.template.id
        )
        template_ctx.create_dms_directory()
        cls.template.refresh()
        cls.directory = cls.template.dms_directory_ids
        cls.subdirectory_1 = cls.env["dms.directory"].create(
            {
                "name": "Test subdirectory 1",
                "parent_id": cls.directory.id,
                "storage_id": cls.storage.id,
            }
        )
        cls.subdirectory_2 = cls.env["dms.directory"].create(
            {
                "name": "Test subdirectory 2",
                "parent_id": cls.directory.id,
                "storage_id": cls.storage.id,
            }
        )
        cls.partner = (
            cls.env["res.partner"]
            .with_context(skip_track_dms_field_template=True)
            .create({"name": "DEMO Partner"})
        )

    def _create_directory_vals(self, record):
        return {
            "storage_id": self.storage.id,
            "is_root_directory": True,
            "name": record.display_name,
            "res_model": record._name,
            "res_id": record.id,
        }

    def test_check_constrain_multi_directory(self):
        self.env["dms.directory"].create(self._create_directory_vals(self.partner))
        with self.assertRaises(ValidationError):
            self.env["dms.directory"].create(self._create_directory_vals(self.partner))

    def test_check_constrain_not_root(self):
        directory = self.env["dms.directory"].create(
            self._create_directory_vals(self.partner)
        )
        with self.assertRaises(ValidationError):
            self.env["dms.directory"].create(
                {
                    "parent_id": directory.id,
                    "name": "Second Directory",
                    "res_model": self.partner._name,
                    "res_id": self.partner.id,
                }
            )

    def test_js_tree(self):
        self.assertTrue(
            any(
                r["id"] == "storage_%s" % self.storage.id
                for r in self.storage.get_js_tree_data()
            )
        )

    def test_template_directory(self):
        self.assertTrue(self.template.dms_directory_ids)
        self.assertIn(
            self.template.group_ids, self.template.dms_directory_ids.group_ids
        )

    def test_creation_process_01(self):
        self.assertFalse(self.partner.dms_directory_ids)
        template = self.env["dms.field.template"].with_context(
            res_model=self.partner._name, res_id=self.partner.id
        )
        template.create_dms_directory()
        self.partner.refresh()
        self.assertEqual(self.partner.dms_directory_ids.name, self.partner.display_name)
        child_names = self.partner.dms_directory_ids.mapped("child_directory_ids.name")
        directory_0 = self.partner.dms_directory_ids[0]
        self.assertNotIn(self.template.group_ids, directory_0.group_ids)
        self.assertIn(self.group, directory_0.group_ids.group_ids)
        self.assertIn(self.user_b, directory_0.group_ids.explicit_user_ids)
        self.assertIn(self.user_a, directory_0.group_ids.users)
        self.assertIn(self.user_b, directory_0.group_ids.users)
        self.assertIn(self.subdirectory_1.name, child_names)
        self.assertIn(self.subdirectory_2.name, child_names)
        with self.assertRaises(ValidationError):
            template.create_dms_directory()

    def test_creation_process_02(self):
        partner_1 = self.env["res.partner"].create({"name": "Test partner 1"})
        partner_1.refresh()
        self.assertTrue(partner_1.dms_directory_ids)
        partner_2 = (
            self.env["res.partner"]
            .with_context(skip_track_dms_field_template=True)
            .create({"name": "Test partner 2"})
        )
        partner_2.refresh()
        self.assertFalse(partner_2.dms_directory_ids)

    def test_creation_process_03(self):
        self.template.directory_format_name = "{{object.name}}-{{object.ref}}"
        partner_1 = self.env["res.partner"].create(
            {"name": "TEST-PARTNER1", "ref": "CUSTOM-REF"}
        )
        partner_1.refresh()
        self.assertEqual(
            partner_1.dms_directory_ids.name, "%s-%s" % (partner_1.name, partner_1.ref)
        )

    def test_parents(self):
        directory = self.env["dms.directory"].create(
            self._create_directory_vals(self.partner)
        )
        self.assertEqual(
            directory.search_read_parents([("id", "=", directory.id)], fields=["id"])[
                0
            ],
            {"id": directory.id},
        )
        self.assertEqual(
            directory.search_read_parents(
                [("id", "=", directory.id)], fields=["id", "name"]
            )[0],
            {"id": directory.id, "name": directory.name},
        )
        self.assertIn(
            {"id": directory.id, "name": directory.name},
            directory.search_read_parents(fields=["id", "name"]),
        )
