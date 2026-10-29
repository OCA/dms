# Copyright 2021-2025 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

import odoo.tests
from odoo.exceptions import AccessError
from odoo.tests.common import new_test_user, users
from odoo.tools import mute_logger

from .common import StorageAttachmentBaseCase


@odoo.tests.tagged("post_install", "-at_install")
class TestDmsPortal(odoo.tests.HttpCase, StorageAttachmentBaseCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Name the partner-model root directory "Partners" (the base creates it
        # with a uuid name) so the portal tour can navigate to it by name.
        cls.directory_model.search(
            [
                ("storage_id", "=", cls.storage.id),
                ("res_model", "=", "res.partner"),
                ("is_root_directory", "=", True),
            ],
            limit=1,
        ).name = "Partners"
        cls.portal_user = cls.env["res.users"].search(
            [("login", "=", "portal")], limit=1
        ) or new_test_user(
            cls.env, login="portal", password="portal", groups="base.group_portal"
        )
        cls.partner = cls.portal_user.partner_id
        # The partner's directory is named after the partner; set it before
        # creating the attachment so the tour finds the "Joel Willis" directory.
        cls.partner.name = "Joel Willis"
        cls._create_attachment("test.txt")
        cls._create_attachment("test2.txt", cls.other_partner)
        cls.directory_partner = cls._get_partner_directory()
        cls.other_directory_partner = cls._get_partner_directory(cls.other_partner)
        cls.file_partner = cls.directory_partner.file_ids[0]
        cls.other_file_partner = cls.other_directory_partner.file_ids[0]
        # A portal-accessible "Mails" root directory + file, for the mail tour
        # (replaces the demo "Mails" directory it relied on).
        portal_access = cls.access_group_model.create(
            {
                "name": "Portal Tour",
                "group_ids": [(6, 0, [cls.env.ref("base.group_portal").id])],
            }
        )
        cls.mails_directory = cls.directory_model.create(
            {
                "name": "Mails",
                "is_root_directory": True,
                "storage_id": cls.create_storage(save_type="database").id,
                "group_ids": [(6, 0, [portal_access.id])],
            }
        )
        cls.file_model.create(
            {
                "name": "Mail_01.eml",
                "directory_id": cls.mails_directory.id,
                "content": cls.content_base64(),
            }
        )
        # Flush the computed access relations (dms_*_rel) to the DB so the
        # tour's browser requests — which read them via raw SQL in a separate
        # env — see the portal user's access to these directories.
        cls.env.flush_all()

    def test_access_portal(self):
        self.authenticate("portal", "portal")
        # 404: Incorrect access_token
        file_text = self.create_file(directory=self.directory_partner)
        url = f"{file_text.access_url}&access_token=abc-def"
        response = self.url_open(url, timeout=20)
        self.assertEqual(
            response.status_code, 404, "Can't access file with incorrect access_token"
        )
        # 200
        response = self.url_open(self.file_partner._get_share_url(), timeout=20)
        self.assertEqual(
            response.status_code, 200, "Can access file with correct access_token"
        )
        # 200
        response = self.url_open(self.directory_partner._get_share_url(), timeout=20)
        self.assertEqual(
            response.status_code, 200, "Can access directory with correct access_token"
        )

    def test_tour(self):
        for tour in ("dms_portal_mail_tour", "dms_portal_partners_tour"):
            with self.subTest(tour=tour):
                self.start_tour("/my/dms", tour, login="portal")

    @users("portal")
    @mute_logger("odoo.addons.base.models.ir_access")
    def test_permission_portal_user_access_own_attachment(self):
        """
        The user can access its own attachments, even if its access group are not set
        """
        # Has to manually su=False because the portal user is not a superuser,
        # but odoo uses somewhere sudo() internally
        file = self.file_partner.with_user(self.env.user).with_env(self.env(su=False))
        directory = self.directory_partner.with_user(self.env.user).with_env(
            self.env(su=False)
        )
        # Portal user can only read
        file.check_access("read")

        # Portal user can't do anything else (each operation checked on its own
        # so a single early raise can't mask the others).
        with self.assertRaises(AccessError, msg="Portal user should not write"):
            file.check_access("write")
        with self.assertRaises(AccessError, msg="Portal user should not unlink"):
            file.check_access("unlink")
        with self.assertRaises(AccessError, msg="Portal user should not create"):
            directory.check_access("create")

    @users("portal")
    @mute_logger("odoo.addons.base.models.ir_access")
    def test_permission_portal_user_access_other_attachment(self):
        """
        The user can't access other attachments if its access group are not set
        """
        # Has to manually su=False because the portal user is not a superuser,
        # but odoo uses somewhere sudo() internally
        file = self.other_file_partner.with_user(self.env.user).with_env(
            self.env(su=False)
        )
        # file.invalidate_recordset()
        # Portal user can't do anything
        with self.assertRaises(AccessError, msg="Portal user should not have access"):
            file.check_access("read")
        with self.assertRaises(AccessError, msg="Portal user should not have access"):
            file.check_access("write")
        with self.assertRaises(AccessError, msg="Portal user should not have access"):
            file.check_access("unlink")

    @users("portal")
    @mute_logger("odoo.addons.base.models.ir_access")
    def test_binary_access_token(self):
        """Binary streaming (``/web/image``) honors DMS access tokens.

        Odoo 19 replaced ``ir.binary._find_record_check_access()`` with the
        ``_can_return_content()`` record hook: without the DMS override,
        portal icons/previews of shared records break for users without
        read access.
        """
        file_sudo = self.other_file_partner.sudo()
        token = file_sudo._portal_ensure_token()
        binary = self.env["ir.binary"].with_env(self.env(su=False))
        # Sanity: without a token the record is not reachable
        with self.assertRaises(AccessError):
            binary._find_record(
                res_model="dms.file", res_id=file_sudo.id, field="image_128"
            )
        # A valid token grants (sudo) streaming access
        record = binary._find_record(
            res_model="dms.file",
            res_id=file_sudo.id,
            access_token=token,
            field="image_128",
        )
        self.assertTrue(record.env.su)
        self.assertEqual(record.id, file_sudo.id)
        # Directories resolve tokens too
        directory_sudo = self.other_directory_partner.sudo()
        dir_token = directory_sudo._portal_ensure_token()
        record = binary._find_record(
            res_model="dms.directory",
            res_id=directory_sudo.id,
            access_token=dir_token,
            field="image_128",
        )
        self.assertTrue(record.env.su)

    def test_portal_directory_search(self):
        """Portal directory name search must actually filter.

        Both 18.0 (``expression.OR``) and the ported 19.0 code built
        ``OR([[], [...]])`` — the empty domain is TRUE, so the OR collapsed
        and the search never filtered anything.
        """
        self.authenticate("portal", "portal")
        response = self.url_open("/my/dms?search_in=name&search=zzz-no-match")
        self.assertNotIn(
            "Partners",
            response.text,
            "A non-matching search must filter out the Partners directory",
        )
        response = self.url_open("/my/dms?search_in=name&search=Partners")
        self.assertIn("Partners", response.text)
