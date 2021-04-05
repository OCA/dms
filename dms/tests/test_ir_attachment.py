# Copyright 2021 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import base64

from odoo.tests import common


class IrAttachmentTestCase(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.user_demo = self.browse_ref("base.user_demo")
        self.unprivileged_user = self.env["res.users"].create(
            {
                "name": "unprivileged test user",
                "login": "test",
                "groups_id": [
                    (
                        6,
                        0,
                        [
                            self.env.ref("base.group_user").id,
                            self.env.ref("base.group_partner_manager").id,
                        ],
                    )
                ],
            }
        )
        self.partner = self.env.ref("base.res_partner_12")
        self.attachment = self.env["ir.attachment"]

    def content_base64(self):
        return base64.b64encode(b"\xff data")

    def test_create_attachment(self):
        vals = {
            "name": "Test file",
            "res_model": "res.partner",
            "res_id": self.partner.id,
            "datas": self.content_base64(),
        }
        attachment = self.attachment.sudo(self.unprivileged_user).create(vals)
        self.assertEquals(attachment.name, "Test file")
        vals["name"] = "Test file 2"
        attachment = self.attachment.sudo(self.user_demo).create(vals)
        self.assertEquals(attachment.name, "Test file 2")
