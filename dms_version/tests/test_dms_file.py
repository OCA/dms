# Copyright 2017-2020 MuK IT GmbH
# Copyright 2021-2022 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64

from odoo.addons.dms.tests.common import StorageDatabaseBaseCase


class TestFileVersion(StorageDatabaseBaseCase):
    def setUp(self):
        super().setUp()
        self.storage.has_versioning = True

    def test_file_version(self):
        file_01 = self.create_file(directory=self.directory)
        self.assertFalse(file_01.current_revision_id)
        self.assertTrue(file_01.active)
        file_01.write({"content": base64.b64encode(b"\xff new")})
        self.assertTrue(file_01.current_revision_id)
        self.assertFalse(file_01.active)
        self.assertTrue(file_01.current_revision_id.active)
        self.assertEqual(file_01.current_revision_id.revision_number, 1)
        self.assertIn(file_01, file_01.current_revision_id.old_revision_ids)
        self.assertEqual(file_01.current_revision_id.revision_count, 1)
