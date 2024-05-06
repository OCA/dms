# Copyright 2020 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError
from odoo.tests import SavepointCase


class TestDmsField(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.storage = cls.env["dms.storage"].create(
            {
                "name": "DMS Storage",
                "model_ids": [(4, cls.env.ref("base.model_res_partner").id)],
                "save_type": "database",
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "DEMO Partner"})

    def _create_directory_vals(self, record):
        return {
            "root_storage_id": self.storage.id,
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
                    "root_storage_id": self.storage.id,
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
                "root_storage_id": self.storage.id,
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
            default_res_id=self.partner.id, default_res_model=self.partner._name,
        ).create({"storage_id": self.storage.id}).create_directory()
        self.partner.refresh()
        self.assertTrue(self.partner.dms_directory_ids)
        self.assertEqual(self.storage, self.partner.dms_directory_ids.root_storage_id)
