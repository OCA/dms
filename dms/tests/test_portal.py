# Copyright 2021-2022 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

import odoo.tests
from odoo.tests.common import users

from .common import StorageAttachmentBaseCase


@odoo.tests.tagged("post_install", "-at_install")
class TestDmsPortal(odoo.tests.HttpCase, StorageAttachmentBaseCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env.ref("base.partner_demo_portal")
        self.portal_user = self.partner.user_ids
        self.portal_user.login = "portal"
        self._create_attachment("test.txt")
        self.directory_partner = self._get_partner_directory()
        self.file_partner = self.directory_partner.file_ids[0]

    def test_access_portal(self):
        self.authenticate("portal", "portal")
        # 404: Incorrect access_token
        file_text = self.create_file(directory=self.directory_partner)
        url = "%s&access_token=abc-def" % (file_text.access_url)
        response = self.url_open(url, timeout=20)
        self.assertEqual(response.status_code, 404)
        # 200
        response = self.url_open(self.file_partner._get_share_url(), timeout=20)
        self.assertEqual(response.status_code, 200)
        # 200
        response = self.url_open(self.directory_partner._get_share_url(), timeout=20)
        self.assertEqual(response.status_code, 200)

    def test_tour(self):
        for tour in ("dms_portal_mail_tour", "dms_portal_partners_tour"):
            with self.subTest(tour=tour):
                self.start_tour("/", tour, login="portal")

    def test_permission_flag(self):
        """Assert portal partner directory and files permissions."""
        # Superuser can read everything
        self.assertTrue(self.directory_partner.permission_read)
        self.assertTrue(self.directory_partner.parent_id.permission_read)
        self.assertTrue(self.file_partner.permission_read)
        self.assertEqual(
            self.directory_partner.parent_id.child_directory_ids, self.directory_partner
        )
        # Public user can access only the empty res.partner folder
        self.directory_partner.with_user(self.public_user).invalidate_cache()
        self.assertFalse(
            self.directory_partner.with_user(self.public_user).permission_read
        )
        self.directory_partner.parent_id.with_user(self.public_user).invalidate_cache()
        self.assertTrue(
            self.directory_partner.parent_id.with_user(self.public_user).permission_read
        )
        self.file_partner.with_user(self.public_user).invalidate_cache()
        self.assertFalse(self.file_partner.with_user(self.public_user).permission_read)
        self.assertFalse(
            self.directory_partner.parent_id.with_user(
                self.public_user
            ).child_directory_ids
        )

    @users("portal")
    def test_permission_flag_portal_user(self):
        # Portal user can read everything (because it belongs to him)
        self.assertTrue(self.directory_partner.permission_read)
        self.assertTrue(self.directory_partner.parent_id.permission_read)
        self.assertTrue(self.file_partner.permission_read)
        self.assertEqual(
            self.directory_partner.parent_id.child_directory_ids,
            self.directory_partner,
        )
