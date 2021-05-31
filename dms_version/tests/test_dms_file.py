# Copyright 2017-2020 MuK IT GmbH
# Copyright 2021 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64

from odoo.addons.dms.tests.common import DocumentsBaseCase, multi_users


class TestFileVersion(DocumentsBaseCase):
    def _setup_test_data(self):
        super()._setup_test_data()
        self.storage_demo = self.env.ref("dms.storage_demo")
        self.storage_demo.sudo().write({"has_versioning": True})

    @multi_users(lambda self: self.multi_users(), callback="_setup_test_data")
    def test_version_revert(self):
        dms_file = self.env.ref("dms.file_13_demo")
        dms_file.write({"content": base64.b64encode(b"\xff new")})
        self.assertEqual(len(dms_file.version_ids.ids), 1)
        self.assertEqual(dms_file.versions_count, 1)
        dms_file.action_revert_version()
        self.assertEqual(len(dms_file.version_ids.ids), 0)
        self.assertEqual(dms_file.versions_count, 0)
        self.assertNotEqual(dms_file.content, base64.b64encode(b"\xff new"))

    @multi_users(lambda self: self.multi_users(), callback="_setup_test_data")
    def test_version_delete(self):
        dms_file = self.env.ref("dms.file_13_demo")
        dms_file.write({"content": self.content_base64()})
        self.assertEqual(len(dms_file.version_ids.ids), 1)
        self.assertEqual(dms_file.versions_count, 1)
        dms_file.action_delete_versions()
        self.assertEqual(len(dms_file.version_ids.ids), 0)
        self.assertEqual(dms_file.versions_count, 0)
