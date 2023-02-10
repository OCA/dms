# Copyright 2023 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import common


class TestDmsAttachmentLink(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env["res.partner"].create({"name": "Test partner"})
        self.dms_file = self.env.ref("dms.file_01_demo")

    def test_add_url_attachment(self):
        attachment = self.dms_file.with_context(
            active_model=self.partner._name,
            active_id=self.partner.id,
        ).action_create_attachment_from_record()
        self.assertEqual(attachment.name, self.dms_file.name)
        self.assertEqual(attachment.datas, self.dms_file.content)
