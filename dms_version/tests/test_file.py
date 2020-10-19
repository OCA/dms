# Copyright 2017-2020 MuK IT GmbH
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64
import logging
import os

from odoo.addons.dms.tests.common import multi_users
from odoo.addons.dms.tests.test_file import FileTestCase

_path = os.path.dirname(os.path.dirname(__file__))
_logger = logging.getLogger(__name__)


class FileVersionTestCase(FileTestCase):
    @multi_users(lambda self: self.multi_users(), callback="_setup_test_data")
    def test_version_revert(self):
        storage = self.create_storage(sudo=True)
        storage.write({"has_versioning": True})
        file = self.create_file(storage=storage)
        file.write({"content": base64.b64encode(b"\xff new")})
        self.assertTrue(len(file.version_ids.exists()) == 1)
        self.assertTrue(file.count_versions == 1)
        file.action_revert_version()
        self.assertTrue(len(file.version_ids.exists()) == 0)
        self.assertTrue(file.count_versions == 0)
        self.assertTrue(file.content == self.content_base64())

    @multi_users(lambda self: self.multi_users(), callback="_setup_test_data")
    def test_version_delete(self):
        storage = self.create_storage(sudo=True)
        storage.write({"has_versioning": True})
        file = self.create_file(storage=storage)
        file.write({"content": self.content_base64()})
        self.assertTrue(len(file.version_ids.exists()) == 1)
        self.assertTrue(file.count_versions == 1)
        file.action_delete_versions()
        self.assertTrue(len(file.version_ids.exists()) == 0)
        self.assertTrue(file.count_versions == 0)
