# Copyright 2023 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import common


class TestDmsAttachmentLink(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env["res.partner"].create({"name": "Test partner"})
        self.dms_file = self.env.ref("dms.file_01_demo")
        ctx = {
            "active_model": self.partner._name,
            "active_id": self.partner.id,
        }
        self.wizard_model = self.env["wizard.ir.attachment.dms.file"].with_context(ctx)

    def test_add_url_attachment(self):
        wizard = self.wizard_model.create({"dms_file_id": self.dms_file.id})
        wizard.action_link()
        domain = [
            ("dms_file_id", "=", self.dms_file.id),
            ("res_model", "=", self.partner._name),
            ("res_id", "=", self.partner.id),
        ]
        attachment = self.env["ir.attachment"].search(domain)
        self.assertEqual(attachment.name, self.dms_file.name)
        self.assertEqual(attachment.datas, self.dms_file.content)
