# Copyright 2026 Ledo Enterprises
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import json

from odoo.tests import new_test_user

from odoo.addons.base.tests.common import BaseCommon
from odoo.addons.dms_spreadsheet.models.dms_file import SPREADSHEET_MIMETYPE


class TestDmsSpreadsheet(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.storage = cls.env["dms.storage"].create(
            {"name": "Test Storage", "save_type": "database"}
        )
        cls.directory = cls.env["dms.directory"].create(
            {
                "name": "Test Directory",
                "storage_id": cls.storage.id,
                "is_root_directory": True,
            }
        )
        # readonly_user: member of DMS access group (can read) but no write access
        cls.readonly_user = new_test_user(cls.env, login="dms-readonly")
        cls.access_group = cls.env["dms.access.group"].create(
            {
                "name": "Test Read-Only",
                "perm_write": False,
                "perm_create": False,
                "explicit_user_ids": [(4, cls.readonly_user.id)],
            }
        )
        cls.directory.group_ids = [(4, cls.access_group.id)]

    def _make_spreadsheet_file(self, name="Test Sheet", content=None):
        vals = {
            "name": name,
            "directory_id": self.directory.id,
            "mimetype": SPREADSHEET_MIMETYPE,
        }
        if content is not None:
            vals["spreadsheet_binary_data"] = content
        return self.env["dms.file"].create(vals)

    # ── Creation ─────────────────────────────────────────────────────────────

    def test_create_sets_handler(self):
        """Creating a dms.file with MIME type sets handler='spreadsheet'."""
        file = self._make_spreadsheet_file()
        self.assertEqual(file.handler, "spreadsheet")

    def test_create_non_spreadsheet_no_handler(self):
        """A regular dms.file has no handler set."""
        file = self.env["dms.file"].create(
            {
                "name": "plain.txt",
                "directory_id": self.directory.id,
                "content": base64.b64encode(b"hello"),
            }
        )
        self.assertFalse(file.handler)

    # ── open_spreadsheet action ───────────────────────────────────────────────

    def test_open_spreadsheet_action(self):
        """open_spreadsheet() returns a client action with the correct tag."""
        file = self._make_spreadsheet_file()
        action = file.open_spreadsheet()
        self.assertEqual(action["type"], "ir.actions.client")
        self.assertEqual(action["tag"], "action_spreadsheet_oca")
        self.assertEqual(action["params"]["spreadsheet_id"], file.id)
        self.assertEqual(action["params"]["model"], "dms.file")

    # ── get_spreadsheet_data ──────────────────────────────────────────────────

    def test_get_spreadsheet_data_empty(self):
        """A brand-new spreadsheet returns data dict, no revisions, normal mode."""
        file = self._make_spreadsheet_file()
        data = file.get_spreadsheet_data()
        # spreadsheet.abstract may initialise spreadsheet_binary_data with a
        # default empty document — we just verify it's a dict
        self.assertIsInstance(data["spreadsheet_raw"], dict)
        self.assertEqual(data["revisions"], [])
        self.assertEqual(data["mode"], "normal")
        self.assertEqual(data["name"], "Test Sheet")

    def test_get_spreadsheet_data_with_content(self):
        """A file with JSON content returns the decoded dict."""
        payload = {"version": 1, "sheets": []}
        encoded = base64.b64encode(json.dumps(payload).encode())
        file = self._make_spreadsheet_file(content=encoded)
        data = file.get_spreadsheet_data()
        self.assertEqual(data["spreadsheet_raw"], payload)

    def test_get_spreadsheet_data_readonly(self):
        """A user with read-only DMS access gets mode='readonly'."""
        file = self._make_spreadsheet_file()
        data = file.with_user(self.readonly_user).get_spreadsheet_data()
        self.assertEqual(data["mode"], "readonly")

    # ── Content bridge ────────────────────────────────────────────────────────

    def test_content_bridge_compute(self):
        """Reading content on a spreadsheet file returns spreadsheet_binary_data."""
        payload = base64.b64encode(json.dumps({"test": True}).encode())
        file = self._make_spreadsheet_file(content=payload)
        self.assertEqual(file.content, payload)

    def test_content_bridge_inverse(self):
        """Writing content on a spreadsheet file updates spreadsheet_binary_data."""
        file = self._make_spreadsheet_file()
        new_payload = base64.b64encode(json.dumps({"updated": True}).encode())
        file.content = new_payload
        self.assertEqual(file.spreadsheet_binary_data, new_payload)

    def test_non_spreadsheet_content_unaffected(self):
        """Regular files use the normal content compute path."""
        raw = b"plain text"
        encoded = base64.b64encode(raw)
        file = self.env["dms.file"].create(
            {
                "name": "notes.txt",
                "directory_id": self.directory.id,
                "content": encoded,
            }
        )
        # handler is not 'spreadsheet', so spreadsheet bridge must not interfere
        self.assertNotEqual(file.handler, "spreadsheet")
        # content should round-trip correctly
        self.assertEqual(base64.b64decode(file.content), raw)

    # ── Mimetype ──────────────────────────────────────────────────────────────

    def test_mimetype_forced_for_spreadsheet_handler(self):
        """handler='spreadsheet' forces mimetype to application/o-spreadsheet."""
        file = self._make_spreadsheet_file()
        file.invalidate_recordset()
        self.assertEqual(file.mimetype, SPREADSHEET_MIMETYPE)

    def test_write_sets_handler_on_mimetype_change(self):
        """Updating mimetype to o-spreadsheet via write() sets handler."""
        file = self.env["dms.file"].create(
            {
                "name": "doc.txt",
                "directory_id": self.directory.id,
                "content": base64.b64encode(b"x"),
            }
        )
        self.assertFalse(file.handler)
        file.write({"mimetype": SPREADSHEET_MIMETYPE})
        self.assertEqual(file.handler, "spreadsheet")

    def test_get_spreadsheet_data_corrupted(self):
        """Corrupted binary data does not crash — returns empty dict."""
        file = self._make_spreadsheet_file(content=base64.b64encode(b"not valid json"))
        with self.assertLogs("odoo.addons.dms_spreadsheet.models.dms_file", "WARNING"):
            data = file.get_spreadsheet_data()
        self.assertEqual(data["spreadsheet_raw"], {})

    # ── Wizard ────────────────────────────────────────────────────────────────

    def test_wizard_create_spreadsheet(self):
        """Wizard creates dms.file with correct attributes and opens editor."""
        wizard = self.env["dms.spreadsheet.create"].create(
            {
                "name": "Quarterly Budget",
                "directory_id": self.directory.id,
            }
        )
        action = wizard.action_create_spreadsheet()
        created = self.env["dms.file"].search(
            [
                ("name", "=", "Quarterly Budget"),
                ("directory_id", "=", self.directory.id),
            ]
        )
        self.assertTrue(created)
        self.assertEqual(created.handler, "spreadsheet")
        self.assertEqual(created.mimetype, SPREADSHEET_MIMETYPE)
        self.assertEqual(action["type"], "ir.actions.client")
        self.assertEqual(action["tag"], "action_spreadsheet_oca")

    def test_wizard_default_get_from_context(self):
        """Wizard pre-fills directory_id from context."""
        wizard = (
            self.env["dms.spreadsheet.create"]
            .with_context(default_directory_id=self.directory.id)
            .new({})
        )
        self.assertEqual(wizard.directory_id, self.directory)
