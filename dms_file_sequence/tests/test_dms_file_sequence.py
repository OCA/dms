# Copyright 2025 APSL-Nagarro - Miquel Alzanillas, Antoni Marroig
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from freezegun import freeze_time
from psycopg2 import IntegrityError

from odoo.tests.common import Form, new_test_user
from odoo.tools import mute_logger

from odoo.addons.dms.tests.common import StorageDatabaseBaseCase


@freeze_time("2023-01-01 12:00:00")
class TestDMSFileSequence(StorageDatabaseBaseCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.file_seq = cls.env.ref("dms_file_sequence.dms_file_sequence")
        cls.file_model = cls.env["dms.file"]
        cls.access_group_model = cls.env["dms.access.group"]
        cls.subdirectory = cls.create_directory(directory=cls.directory)
        cls.user_a = new_test_user(cls.env, login="user_a", groups="dms.group_dms_user")
        cls.group_a = cls.access_group_model.create(
            {
                "name": "Group A",
                "perm_create": True,
                "explicit_user_ids": [(6, 0, [cls.user_a.id])],
                "directory_ids": [
                    (4, cls.directory.id),
                    (4, cls.subdirectory.id),
                ],
            }
        )
        cls.directory.group_ids = [(4, cls.group_a.id)]

    def setUp(self):
        super().setUp()
        self.file_model.sudo().search([]).unlink()
        self.file_seq._get_current_sequence().number_next = 11

    def test_sequence_after_creation(self):
        """Sequence is applied only after file creation."""
        file_f = Form(self.file_model)
        file_f.content = b"hola"
        file_f.directory_id = self.subdirectory
        self.assertFalse(file_f.name)
        self.assertFalse(file_f.sequence_code)
        dms_file = file_f.save()
        self.assertTrue(dms_file.sequence_code)
        self.assertEqual(dms_file.name, dms_file.sequence_code)
        self.assertEqual(dms_file.sequence_code, "23-00011")
        self.assertEqual(dms_file.display_name, "23-00011")

    def test_sequence_not_copied_to_another_file(self):
        """Sequence is not duplicated to another file."""
        file1 = self.file_model.create(
            {"name": "Document 1", "directory_id": self.directory.id}
        )
        file2 = file1.copy()
        self.assertEqual(file1.sequence_code, "23-00011")
        self.assertEqual(file2.sequence_code, "23-00012")

    @mute_logger("odoo.sql_db")
    def test_sequence_unique(self):
        """Sequence cannot have duplicates."""
        file1 = self.create_file(self.directory)
        self.assertEqual(file1.sequence_code, "23-00011")
        self.file_seq._get_current_sequence().number_next = 11
        with self.assertRaises(IntegrityError), self.env.cr.savepoint():
            self.file_model.create(
                {"name": "Document 2", "directory_id": self.directory.id}
            )

    def test_file_without_sequence(self):
        """Preexisting files had no sequence, and they should display fine."""
        file1 = self.file_model.create(
            {
                "name": "Legacy Document",
                "sequence_code": False,
                "directory_id": self.directory.id,
            }
        )
        self.assertEqual(file1.display_name, "Legacy Document")
        self.assertFalse(file1.sequence_code)
        # Ensure the sequence does not increment
        file2 = self.file_model.create(
            {"name": "New Document", "directory_id": self.directory.id}
        )
        self.assertEqual(file2.sequence_code, "23-00011")
        self.assertEqual(file2.display_name, "23-00011 - New Document")

    def test_custom_pattern(self):
        """Display name pattern can be customized."""
        self.env["ir.config_parameter"].set_param(
            "dms_file_sequence.display_name_pattern", "%(name)s/%(sequence_code)s"
        )
        dms_file = self.file_model.create(
            {"name": "Custom File", "directory_id": self.directory.id}
        )
        self.assertEqual(dms_file.display_name, "Custom File/23-00011")
        self.assertEqual(dms_file.sequence_code, "23-00011")
        self.env["ir.config_parameter"].set_param(
            "dms_file_sequence.display_name_pattern", "%(name)s"
        )
        dms_file = self.file_model.create(
            {"name": "Another File", "directory_id": self.directory.id}
        )
        self.assertEqual(dms_file.display_name, "Another File")
        self.assertEqual(dms_file.sequence_code, "23-00012")
        self.env["ir.config_parameter"].set_param(
            "dms_file_sequence.display_name_pattern", "%(sequence_code)s"
        )
        dms_file = self.file_model.create(
            {"name": "Final File", "directory_id": self.directory.id}
        )
        self.assertEqual(dms_file.display_name, "23-00013")
        self.assertEqual(dms_file.sequence_code, "23-00013")

    def test_name_search(self):
        """Allow searching by sequence code by default."""
        file1 = self.file_model.create(
            {"name": "Document A", "directory_id": self.directory.id}
        )
        self.assertEqual(file1.sequence_code, "23-00011")
        file2 = self.file_model.create(
            {"name": "Document B", "directory_id": self.directory.id}
        )
        self.assertEqual(file2.sequence_code, "23-00012")
        file3 = self.file_model.create(
            {"name": "Document C", "directory_id": self.directory.id}
        )
        self.assertEqual(file3.sequence_code, "23-00013")

        # Search by name
        results = self.file_model.name_search("Document B")
        self.assertIn((file2.id, "23-00012 - Document B"), results)
        self.assertNotIn((file1.id, "23-00011 - Document A"), results)
        self.assertNotIn((file3.id, "23-00013 - Document C"), results)

        # Search by sequence code
        results = self.file_model.name_search("23-00012")
        self.assertIn((file2.id, "23-00012 - Document B"), results)
        self.assertNotIn((file1.id, "23-00011 - Document A"), results)
        self.assertNotIn((file3.id, "23-00013 - Document C"), results)
