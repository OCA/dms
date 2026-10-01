# Copyright 2026 Keith Brandenburg
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.dms.tests.common import StorageDatabaseBaseCase


class TestDmsFileDescription(StorageDatabaseBaseCase):
    def test_description_short(self):
        self.file.description = (
            "  This is a long\nfile description that should be normalized "
            "and shortened.  "
        )

        self.assertEqual(
            self.file.description_short,
            "This is a long file description tha...",
        )

    def test_description_short_empty(self):
        self.file.description = False

        self.assertFalse(self.file.description_short)

    def test_description_search_filters(self):
        arch, _view = self.file_model._get_view(view_type="search")

        self.assertTrue(arch.xpath(".//filter[@name='has_description']"))
        self.assertTrue(arch.xpath(".//filter[@name='missing_description']"))

    def test_description_form_placeholder(self):
        arch, _view = self.file_model._get_view(view_type="form")

        description = arch.xpath(".//field[@name='description']")[0]
        self.assertEqual(description.get("placeholder"), "Description")
