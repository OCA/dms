# Copyright 2017-2020 MuK IT GmbH
# Copyright 2021-2022 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import logging

from odoo.exceptions import UserError
from odoo.tests import Form

from odoo.addons.dms.tests.common import StorageDatabaseBaseCase

_logger = logging.getLogger(__name__)


class TestFileVersion(StorageDatabaseBaseCase):
    def setUp(self):
        super().setUp()
        self.storage.has_versioning = True
        self.my_directory = self.create_directory(storage=self.storage)

    def test_01_onchange_events_of_directory(self):
        self.assertTrue(self.my_directory.has_versioning)
        self.my_sub1_directory = self.create_directory(
            storage=self.storage, directory=self.my_directory
        )
        self.assertTrue(self.my_sub1_directory.has_versioning)
        self.my_directory.has_versioning = False
        self.my_sub2_directory = self.create_directory(
            storage=self.storage, directory=self.my_directory
        )
        self.assertFalse(self.my_sub2_directory.has_versioning)

    def test_02_file_version(self):
        self.assertTrue(self.my_directory.has_versioning)
        _logger.info("Step 1: Create file_01 and file_02")
        file_01 = self.create_file(directory=self.my_directory)
        self.assertFalse(file_01.current_revision_id)
        self.assertTrue(file_01.active)
        self.assertTrue(file_01.has_versioning)
        file_01.write({"content": base64.b64encode(b"\xff new_1")})
        self.assertFalse(file_01.active)
        self.assertTrue(file_01.current_revision_id.active)
        self.assertEqual(file_01.current_revision_id.revision_number, 1)
        self.assertEqual(file_01.origin_id, file_01)
        file_02 = file_01.current_revision_id
        self.assertEqual(file_02.origin_id, file_01)
        self.assertEqual(file_02.parent_id, file_01)

        _logger.info("Step 2: Create file_03 and file_04")
        file_02.write({"content": base64.b64encode(b"\xff new_2")})
        file_03 = file_01.current_revision_id
        file_03.write({"content": base64.b64encode(b"\xff new_3")})
        file_04 = file_01.current_revision_id
        self.assertEqual(file_01.all_revision_count, 3)
        self.assertIn(file_02, file_01.all_revision_ids)
        self.assertIn(file_03, file_01.all_revision_ids)
        self.assertIn(file_04, file_01.all_revision_ids)

        logs = """
        # Check values in following table
        #           id  origin_id  parent_id  current_revision_id  version_number  active
        # file_01    1      1        False            4               0             False
        # file_02    2      1          1              4               1             False
        # file_03    3      1          2              4               2             False
        # file_04    4      1          3             False            3             True
        """
        _logger.info(logs)
        self.assertEqual(file_01.origin_id, file_01)
        self.assertFalse(file_01.parent_id)
        self.assertEqual(file_01.current_revision_id, file_04)
        self.assertFalse(file_01.active)
        self.assertEqual(file_01.revision_number, 0)
        self.assertEqual(file_02.origin_id, file_01)
        self.assertEqual(file_02.parent_id, file_01)
        self.assertEqual(file_02.current_revision_id, file_04)
        self.assertFalse(file_02.active)
        self.assertEqual(file_02.revision_number, 1)
        self.assertEqual(file_03.origin_id, file_01)
        self.assertEqual(file_03.parent_id, file_02)
        self.assertEqual(file_03.current_revision_id, file_04)
        self.assertFalse(file_03.active)
        self.assertEqual(file_03.revision_number, 2)
        self.assertEqual(file_04.origin_id, file_01)
        self.assertEqual(file_04.parent_id, file_03)
        self.assertFalse(file_04.current_revision_id)
        self.assertTrue(file_04.active)
        self.assertEqual(file_04.revision_number, 3)

        _logger.info("Step 3: Restore file_02")
        wizard = Form(
            self.env["restore.old.revision"].with_context(active_id=file_02.id)
        ).save()
        wizard.action_done()
        logs = """
        # Check values in following table
        #           id   current_revision_id  active
        # file_01    1           2             False
        # file_02    2         False           True
        # file_03    3           2             False
        # file_04    4           2             False
        """
        _logger.info(logs)
        self.assertEqual(file_01.current_revision_id, file_02)
        self.assertFalse(file_02.current_revision_id)
        self.assertEqual(file_03.current_revision_id, file_02)
        self.assertEqual(file_04.current_revision_id, file_02)
        self.assertFalse(file_01.active)
        self.assertTrue(file_02.active)
        self.assertFalse(file_03.active)
        self.assertFalse(file_04.active)
        _logger.info("Step 4: Create file_05")
        file_02.write({"content": base64.b64encode(b"\xff new_4")})
        file_05 = file_01.current_revision_id
        logs = """
        # Check values in following table
        #           id  origin_id  parent_id  current_revision_id  version_number  active
        # file_01    1      1        False            5               0             False
        # file_02    2      1          1              5               1             False
        # file_03    3      1          2              5               2             False
        # file_04    4      1          3              5               3             False
        # file_05    5      1          2             False            4             True
        """
        _logger.info(logs)
        self.assertEqual(file_01.origin_id, file_01)
        self.assertFalse(file_01.parent_id)
        self.assertEqual(file_01.current_revision_id, file_05)
        self.assertFalse(file_01.active)
        self.assertEqual(file_01.revision_number, 0)
        self.assertEqual(file_02.origin_id, file_01)
        self.assertEqual(file_02.parent_id, file_01)
        self.assertEqual(file_02.current_revision_id, file_05)
        self.assertFalse(file_02.active)
        self.assertEqual(file_02.revision_number, 1)
        self.assertEqual(file_03.origin_id, file_01)
        self.assertEqual(file_03.parent_id, file_02)
        self.assertEqual(file_03.current_revision_id, file_05)
        self.assertFalse(file_03.active)
        self.assertEqual(file_03.revision_number, 2)
        self.assertEqual(file_04.origin_id, file_01)
        self.assertEqual(file_04.parent_id, file_03)
        self.assertEqual(file_04.current_revision_id, file_05)
        self.assertFalse(file_04.active)
        self.assertEqual(file_04.revision_number, 3)
        self.assertEqual(file_05.origin_id, file_01)
        self.assertEqual(file_05.parent_id, file_02)
        self.assertFalse(file_05.current_revision_id)
        self.assertTrue(file_05.active)
        self.assertEqual(file_05.revision_number, 4)

        _logger.info("check_unique_name_revision_number")
        error_message = "Reference and revision must be unique in a directory."
        with self.assertRaises(UserError, msg=error_message):
            file_04.write({"revision_number": 1})

        _logger.info("check_unique_origin_revision_number")
        error_message = 'Revision number "1" must be unique.'
        with self.assertRaises(UserError, msg=error_message):
            file_04.write({"revision_number": 1})

        _logger.info("check_set_file_active_with_function_write")
        error_message = "Please use the restore button to activate this revision."
        with self.assertRaises(UserError, msg=error_message):
            file_04.write({"active": True})

        _logger.info("check_unique_active_file")
        error_message = 'Found more active version of file "%s".' % (file_01.name)
        with self.assertRaises(UserError, msg=error_message):
            file_04.with_context(restore_old_revision=True).write({"active": True})

        _logger.info("check_action_view_revision")
        expected_domain = [
            "&",
            ("id", "in", file_01.all_revision_ids.ids),
            "|",
            ("active", "=", False),
            ("active", "=", True),
        ]
        action = file_05.action_view_revision()
        self.assertEqual(action["domain"], expected_domain)
