# Copyright 2017-2020 MuK IT GmbH
# Copyright 2021 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.addons.dms.tests.common import multi_users
from odoo.addons.dms.tests.test_storage import StorageLObjectTestCase


class StorageVersionTestCase(StorageLObjectTestCase):
    def setUp(self):
        super().setUp()
        self.version = self.env["dms.version"]
        new_storage = self.create_storage(sudo=True)
        new_storage.write({"has_versioning": True})
        self.root_directory = self.env["dms.directory"].create(
            {
                "name": "Test root directory",
                "is_root_directory": True,
                "storage_id": new_storage.id,
                "group_ids": [(6, 0, [self.env.ref("dms.access_group_01_demo").id])],
            }
        )

    @multi_users(lambda self: self.multi_users(), callback="_setup_test_data")
    def test_version_misc(self):
        dms_file = self.create_file(directory=self.root_directory)
        for _ in range(5):
            dms_file.write({"content": self.content_base64()})
        self.assertEqual(len(dms_file.version_ids.ids), 5)
        for version in dms_file.version_ids:
            self.assertEqual(version.content, self.content_base64())
