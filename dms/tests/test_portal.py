# Copyright 2021 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

import base64

import odoo.tests
from odoo.tests import common
from odoo.tests.common import HttpCase


@odoo.tests.tagged("post_install", "-at_install")
class TestDmsPortal(common.SavepointCase, HttpCase):
    def setUp(self):
        super().setUp()
        self.public_user = self.env.ref("base.public_user")
        self.user_admin = self.env.ref("base.user_admin")
        self.file_text = self.env.ref("dms.file_13_demo")
        self.model_partner = self.env.ref("base.model_res_partner")
        storage = self.env.ref("dms.storage_attachment_demo")
        self.partner = self.env.ref("base.partner_demo_portal")
        self._create_attachment("test.txt", self.user_admin.id)
        self.directory_partner = storage.storage_directory_ids.filtered(
            lambda x: (
                x.res_model == self.model_partner.model and x.res_id == self.partner.id
            )
        )
        self.file_partner = self.directory_partner.file_ids[0]

    def content_base64(self):
        return base64.b64encode(b"\xff data")

    def _create_attachment(self, name, uid):
        return (
            self.env["ir.attachment"]
            .with_user(uid)
            .create(
                {
                    "name": name,
                    "res_model": self.model_partner.model,
                    "res_id": self.partner.id,
                    "datas": self.content_base64(),
                }
            )
        )

    def test_access_portal(self):
        self.authenticate("portal", "portal")
        # 404: Incorrect access_token
        url = "%s&access_token=abc-def" % (self.file_text.access_url)
        response = self.url_open(url, timeout=20)
        self.assertEqual(response.status_code, 404)
        # 200
        response = self.url_open(self.file_partner._get_share_url(), timeout=20)
        self.assertEqual(response.status_code, 200)
        # 200
        response = self.url_open(self.directory_partner._get_share_url(), timeout=20)
        self.assertEqual(response.status_code, 200)

    def test_tour(self):
        self.start_tour("/", "dms_portal_mail_tour", login="portal")
        self.start_tour("/", "dms_portal_partners_tour", login="portal")
