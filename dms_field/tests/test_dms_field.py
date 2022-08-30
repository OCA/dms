# Copyright 2020 Creu Blanca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase


class TestDmsField(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.access_group = cls.env["dms.access.group"].create(
            {
                "name": "Access Group",
                "group_ids": [(4, cls.env.ref("base.group_user").id)],
            }
        )
        cls.storage = cls.env["dms.storage"].create(
            {
                "name": "DMS Storage",
                "model_ids": [(4, cls.env.ref("base.model_res_partner").id)],
                "save_type": "database",
                "field_default_group_id": cls.access_group.id,
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "DEMO Partner"})

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

    def test_check_constrain_no_directory(self):
        with self.assertRaises(ValidationError):
            self.env["dms.directory"].create(
                {
                    "storage_id": self.storage.id,
                    "is_root_directory": True,
                    "name": "Test Directory",
                }
            )

    def test_check_constrain_directory_wrong_model(self):
        with self.assertRaises(ValidationError):
            self.env["dms.directory"].create(self._create_directory_vals(self.env.user))

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

    def test_check_constrain_storage_adding(self):
        self.storage.write({"model_ids": [(5, False)]})
        self.env["dms.directory"].create(
            {
                "storage_id": self.storage.id,
                "is_root_directory": True,
                "name": "First Directory",
            }
        )
        with self.assertRaises(ValidationError):
            self.storage.write(
                {"model_ids": [(4, self.env.ref("base.model_res_partner").id)]}
            )

    def test_check_constrain_storage_cleaning(self):
        self.env["dms.directory"].create(self._create_directory_vals(self.partner))
        with self.assertRaises(ValidationError):
            self.storage.write({"model_ids": [(5, False)]})

    def test_creation_wizard(self):
        self.assertFalse(self.partner.dms_directory_ids)
        self.env["dms.add.directory.record"].with_context(
            default_res_id=self.partner.id,
            default_res_model=self.partner._name,
        ).create({"storage_id": self.storage.id}).create_directory()
        self.partner.refresh()
        self.assertTrue(self.partner.dms_directory_ids)
        self.assertEqual(self.storage, self.partner.dms_directory_ids.storage_id)

    def test_js_tree(self):
        self.assertTrue(
            any(
                r["id"] == "storage_%s" % self.storage.id
                for r in self.storage.get_js_tree_data()
            )
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
