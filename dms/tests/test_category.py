# Copyright 2026 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import uuid

from odoo.tests import Form
from odoo.tests.common import users

from .common import DocumentsBaseCase


class Common(DocumentsBaseCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.category = cls.create_category()

    @classmethod
    def create_category(cls):
        category_form = Form(cls.category_model)
        category_form.name = uuid.uuid4().hex
        return category_form.save()


class TestCategory(Common):
    @users("dms-manager", "dms-user")
    def test_code(self):
        self.category.code = code = "TESTCODE"
        self.assertIn(code, self.category.display_name)
        copied_category = self.category.copy()
        self.assertIn(code, copied_category.code)
        # Cleanup for next user
        copied_category.unlink()
