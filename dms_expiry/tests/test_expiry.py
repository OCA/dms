# Copyright 2025 Escodoo, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date, timedelta

from odoo.addons.dms.tests.common import DocumentsBaseCase


class TestExpiry(DocumentsBaseCase):
    def setUp(self):
        super().setUp()
        self.storage = self.create_storage(save_type="database")
        self.directory = self.create_directory(storage=self.storage)
        self.file = self.create_file(directory=self.directory)
        self.date_today = date.today()

    def test_file_with_no_expiry_date(self):
        self.assertEqual(self.file.expiry_date, False)
        self.assertEqual(self.file.days_to_expire, 0)
        self.assertEqual(self.file.expiry_state, False)

    def test_file_valid(self):
        self.file.expiry_date = self.date_today + timedelta(days=40)
        self.assertEqual(self.file.days_to_expire, 40)
        self.assertEqual(self.file.expiry_state, "valid")

    def test_file_expiring_soon(self):
        self.file.expiry_date = self.date_today + timedelta(days=10)
        self.assertEqual(self.file.days_to_expire, 10)
        self.assertEqual(self.file.expiry_state, "expiring_soon")

    def test_file_expired(self):
        self.file.expiry_date = self.date_today - timedelta(days=10)
        self.assertEqual(self.file.days_to_expire, -10)
        self.assertEqual(self.file.expiry_state, "expired")
