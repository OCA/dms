# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from base64 import b64encode
from os import path

from odoo.tests import Form, new_test_user
from odoo.tests.common import users

from odoo.addons.base.tests.common import BaseCommon


class TestDmsFieldAutoClassification(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, test_dms_field=True))
        cls.template = cls.env.ref(
            "dms_field_auto_classification.dms_classification_template_partners"
        )
        cls.user = new_test_user(
            cls.env, login="test_dms_manager_user", groups="dms.group_dms_manager"
        )
        access_group = cls.env.ref("dms.access_group_01_demo")
        access_group.explicit_user_ids = [(4, cls.user.id)]
        cls.env.ref("dms_field.field_template_partner").unlink()
        file_template = cls.env["dms.field.template"].create(
            {
                "name": "Test partner template",
                "storage_id": cls.env.ref("dms.storage_demo").id,
                "model_id": cls.env.ref("base.model_res_partner").id,
                "group_ids": [(4, access_group.id)],
                "directory_format_name": "{{object.vat}}",
            }
        )
        file_template_ctx = file_template.with_context(
            res_model=file_template._name, res_id=file_template.id
        )
        file_template_ctx.create_dms_directory()
        file_template_ctx.invalidate_model()
        cls.partner_a = cls.env["res.partner"].create(
            {
                "name": "Test partner A",
                "vat": "82326033V",
            }
        )
        cls.partner_b = cls.env["res.partner"].create(
            {
                "name": "Test partner B",
                "vat": "58426469Y",
            }
        )
        cls.wizard = cls._create_wizard_dms_classification(cls.template)
        cls.extra_wizard = cls._create_wizard_dms_classification(cls.template)

    @classmethod
    def _data_file(cls, filename, encoding=None):
        mode = "rt" if encoding else "rb"
        with open(path.join(path.dirname(__file__), filename), mode) as file:
            data = file.read()
            if encoding:
                data = data.encode(encoding)
            return b64encode(data)

    @classmethod
    def _create_wizard_dms_classification(cls, template):
        wizard_form = Form(cls.env["wizard.dms.classification"])
        wizard_form.template_id = template
        wizard_form.data_file = cls._data_file("data/test.zip")
        return wizard_form.save()

    def test_partner_misc(self):
        self.assertEqual(self.partner_a.dms_directory_ids.name, "82326033V")
        self.assertEqual(self.partner_b.dms_directory_ids.name, "58426469Y")

    @users("test_dms_manager_user")
    def test_wizard_dms_clasification_process(self):
        self.wizard = self.wizard.with_user(self.env.user)
        self.assertEqual(self.wizard.state, "draft")
        # Wizard - Analyze process
        self.wizard.action_analyze()
        self.assertEqual(self.wizard.state, "analyze")
        self.assertEqual(len(self.wizard.detail_ids), 2)
        file_names = self.wizard.mapped("detail_ids.file_name")
        self.assertIn("82326033V.pdf", file_names)
        self.assertIn("58426469Y.pdf", file_names)
        detail_1 = self.wizard.detail_ids.filtered(
            lambda x: x.file_name == "82326033V.pdf"
        )
        self.assertEqual(detail_1.state, "to_classify")
        self.assertEqual(detail_1.directory_id, self.partner_a.dms_directory_ids)
        self.assertEqual(detail_1.record_ref, self.partner_a)
        detail_2 = self.wizard.detail_ids.filtered(
            lambda x: x.file_name == "58426469Y.pdf"
        )
        self.assertEqual(detail_2.state, "to_classify")
        self.assertEqual(detail_2.directory_id, self.partner_b.dms_directory_ids)
        self.assertEqual(detail_2.record_ref, self.partner_b)
        # Wizard - Classify process
        res = self.wizard.action_classify()
        dms_files = self.env[res["res_model"]].search(res["domain"])
        self.assertEqual(len(dms_files), 2)
        self.assertEqual(
            detail_1.file_id.directory_id, self.partner_a.dms_directory_ids
        )
        self.assertEqual(detail_1.file_id.name, "82326033V.pdf")
        self.assertTrue(detail_1.file_id.content)
        self.assertEqual(detail_1.file_id.res_model, self.partner_a._name)
        self.assertEqual(detail_1.file_id.res_id, self.partner_a.id)
        self.assertEqual(
            detail_2.file_id.directory_id, self.partner_b.dms_directory_ids
        )
        self.assertEqual(detail_2.file_id.name, "58426469Y.pdf")
        self.assertTrue(detail_2.file_id.content)
        self.assertEqual(detail_2.file_id.res_model, self.partner_b._name)
        self.assertEqual(detail_2.file_id.res_id, self.partner_b.id)
        # Extra wizard
        self.extra_wizard = self.extra_wizard.with_user(self.env.user)
        self.assertEqual(self.extra_wizard.state, "draft")
        # New Wizard - Analyze process
        self.extra_wizard.action_analyze()
        self.assertEqual(self.extra_wizard.state, "analyze")
        self.assertEqual(len(self.extra_wizard.detail_ids), 2)
        file_names = self.extra_wizard.mapped("detail_ids.file_name")
        self.assertIn("82326033V.pdf", file_names)
        self.assertIn("58426469Y.pdf", file_names)
        detail_1 = self.extra_wizard.detail_ids.filtered(
            lambda x: x.file_name == "82326033V.pdf"
        )
        self.assertEqual(detail_1.directory_id, self.partner_a.dms_directory_ids)
        self.assertTrue(detail_1.file_id)
        self.assertEqual(detail_1.record_ref, self.partner_a)
        self.assertEqual(detail_1.state, "classified")
        detail_2 = self.extra_wizard.detail_ids.filtered(
            lambda x: x.file_name == "58426469Y.pdf"
        )
        self.assertEqual(detail_2.directory_id, self.partner_b.dms_directory_ids)
        self.assertTrue(detail_2.file_id)
        self.assertEqual(detail_2.record_ref, self.partner_b)
        self.assertEqual(detail_1.state, "classified")
        # New Wizard - Classify process
        res = self.extra_wizard.action_classify()
        new_dms_files = self.env[res["res_model"]].search(res["domain"]) - dms_files
        self.assertEqual(len(new_dms_files), 0)

    @users("test_dms_manager_user")
    def test_wizard_dms_clasification_process_filename_pattern(self):
        self.template.filename_pattern = self.template.filename_pattern.replace(
            ".pdf", ".txt"
        )
        self.assertEqual(self.wizard.state, "draft")
        self.wizard = self.wizard.with_user(self.env.user)
        self.wizard.action_analyze()
        self.assertEqual(self.wizard.state, "analyze")
        self.assertEqual(len(self.wizard.detail_ids), 0)

    @users("test_dms_manager_user")
    def test_wizard_dms_clasification_process_subdirectory(self):
        self.template.directory_pattern = "{0} / Misc"
        # Create subdirectory to partner a
        directory_misc_a = self.env["dms.directory"].create(
            {"name": "Misc", "parent_id": self.partner_a.dms_directory_ids.id}
        )
        # Create subdirectory to partner b
        directory_misc_b = self.env["dms.directory"].create(
            {"name": "Misc", "parent_id": self.partner_b.dms_directory_ids.id}
        )
        # Wizard - Analyze process
        self.wizard = self.wizard.with_user(self.env.user)
        self.wizard.action_analyze()
        self.assertEqual(self.wizard.state, "analyze")
        self.assertEqual(len(self.wizard.detail_ids), 2)
        file_names = self.wizard.mapped("detail_ids.file_name")
        self.assertIn("82326033V.pdf", file_names)
        self.assertIn("58426469Y.pdf", file_names)
        detail_1 = self.wizard.detail_ids.filtered(
            lambda x: x.file_name == "82326033V.pdf"
        )
        self.assertEqual(detail_1.state, "to_classify")
        self.assertEqual(detail_1.directory_id, directory_misc_a)
        self.assertEqual(detail_1.record_ref, self.partner_a)
        detail_2 = self.wizard.detail_ids.filtered(
            lambda x: x.file_name == "58426469Y.pdf"
        )
        self.assertEqual(detail_2.state, "to_classify")
        self.assertEqual(detail_2.directory_id, directory_misc_b)
        self.assertEqual(detail_2.record_ref, self.partner_b)
        # Wizard - Classify process
        res = self.wizard.action_classify()
        dms_files = self.env[res["res_model"]].search(res["domain"])
        self.assertEqual(len(dms_files), 2)
        self.assertEqual(detail_1.file_id.directory_id, directory_misc_a)
        self.assertEqual(detail_2.file_id.directory_id, directory_misc_b)
