# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from base64 import b64encode
from os import path

from odoo.tests import Form, new_test_user
from odoo.tests.common import users

from odoo.addons.base.tests.common import BaseCommon


class TestDmsAutoClassification(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.template = cls.env.ref(
            "dms_auto_classification.dms_classification_template_documents"
        )
        cls.directory = cls.env.ref("dms.directory_01_demo")
        cls.wizard = cls._create_wizard_dms_classification(cls, cls.template)
        cls.extra_wizard = cls._create_wizard_dms_classification(cls, cls.template)
        cls.user = new_test_user(
            cls.env, login="test_dms_user", groups="dms.group_dms_user"
        )
        access_group = cls.env["dms.access.group"].create(
            {
                "name": "Test access group",
                "perm_create": True,
                "perm_write": True,
                "explicit_user_ids": [(4, cls.user.id)],
            }
        )
        cls.directory.group_ids = [(4, access_group.id)]

    def _data_file(self, filename, encoding=None):
        mode = "rt" if encoding else "rb"
        with open(path.join(path.dirname(__file__), filename), mode) as file:
            data = file.read()
            if encoding:
                data = data.encode(encoding)
            return b64encode(data)

    def _create_wizard_dms_classification(self, template):
        wizard_form = Form(self.env["wizard.dms.classification"])
        wizard_form.template_id = template
        wizard_form.data_file = self._data_file(self, "data/test.zip")
        return wizard_form.save()

    @users("test_dms_user")
    def test_wizard_dms_clasification_process(self):
        self.wizard = self.wizard.with_user(self.env.user)
        self.assertEqual(self.wizard.state, "draft")
        # Wizard - Analyze process
        self.wizard.action_analyze()
        self.assertEqual(self.wizard.state, "analyze")
        self.assertEqual(len(self.wizard.detail_ids), 2)
        file_names = self.wizard.mapped("detail_ids.file_name")
        self.assertIn("file-1.txt", file_names)
        self.assertIn("file-2.txt", file_names)
        self.assertIn(self.directory, self.wizard.mapped("detail_ids.directory_id"))
        detail_1 = self.wizard.detail_ids.filtered(
            lambda x: x.file_name == "file-1.txt"
        )
        self.assertEqual(detail_1.state, "to_classify")
        detail_2 = self.wizard.detail_ids.filtered(
            lambda x: x.file_name == "file-2.txt"
        )
        self.assertEqual(detail_2.state, "to_classify")
        # Wizard - Classify process
        res = self.wizard.action_classify()
        dms_files = self.env[res["res_model"]].search(res["domain"])
        self.assertEqual(len(dms_files), 2)
        self.assertEqual(detail_1.state, "classified")
        self.assertEqual(detail_1.file_id.directory_id, self.directory)
        self.assertEqual(detail_1.file_id.name, "file-1.txt")
        self.assertTrue(detail_1.file_id.content)
        self.assertEqual(detail_2.state, "classified")
        self.assertEqual(detail_2.file_id.directory_id, self.directory)
        self.assertEqual(detail_2.file_id.name, "file-2.txt")
        self.assertTrue(detail_2.file_id.content)
        # Extra wizard
        self.assertEqual(self.extra_wizard.state, "draft")
        # New Wizard - Analyze process
        self.extra_wizard = self.extra_wizard.with_user(self.env.user)
        self.extra_wizard.action_analyze()
        self.assertEqual(self.extra_wizard.state, "analyze")
        self.assertEqual(len(self.extra_wizard.detail_ids), 2)
        file_names = self.extra_wizard.mapped("detail_ids.file_name")
        self.assertIn("file-1.txt", file_names)
        self.assertIn("file-2.txt", file_names)
        self.assertIn(
            self.directory, self.extra_wizard.mapped("detail_ids.directory_id")
        )
        detail_1 = self.extra_wizard.detail_ids.filtered(
            lambda x: x.file_name == "file-1.txt"
        )
        self.assertTrue(detail_1.file_id)
        self.assertEqual(detail_1.state, "classified")
        detail_2 = self.extra_wizard.detail_ids.filtered(
            lambda x: x.file_name == "file-2.txt"
        )
        self.assertTrue(detail_2.file_id)
        self.assertEqual(detail_1.state, "classified")
        # New Wizard - Classify process
        res = self.extra_wizard.action_classify()
        dms_files = self.env[res["res_model"]].search(res["domain"])
        self.assertEqual(len(dms_files), 2)

    def test_wizard_dms_clasification_process_filename_pattern(self):
        self.template.filename_pattern = ".pdf$"
        self.assertEqual(self.wizard.state, "draft")
        self.wizard.action_analyze()
        self.assertEqual(self.wizard.state, "analyze")
        self.assertEqual(len(self.wizard.detail_ids), 0)

    @users("test_dms_user")
    def test_wizard_dms_clasification_process_directory_pattern(self):
        self.template.directory_pattern = "Documents2"
        self.assertEqual(self.wizard.state, "draft")
        # Analyze process
        self.wizard = self.wizard.with_user(self.env.user)
        self.wizard.action_analyze()
        self.assertEqual(self.wizard.state, "analyze")
        self.assertEqual(len(self.wizard.detail_ids), 2)
        file_names = self.wizard.mapped("detail_ids.file_name")
        self.assertIn("file-1.txt", file_names)
        self.assertIn("file-2.txt", file_names)
        self.assertNotIn(self.directory, self.wizard.mapped("detail_ids.directory_id"))
        detail_1 = self.wizard.detail_ids.filtered(
            lambda x: x.file_name == "file-1.txt"
        )
        self.assertEqual(detail_1.state, "to_classify")
        detail_2 = self.wizard.detail_ids.filtered(
            lambda x: x.file_name == "file-2.txt"
        )
        self.assertEqual(detail_2.state, "to_classify")
        # Classify process
        res = self.wizard.action_classify()
        dms_files = self.env[res["res_model"]].search(res["domain"])
        self.assertEqual(len(dms_files), 0)
        self.assertFalse(detail_1.file_id)
        self.assertFalse(detail_2.file_id)
