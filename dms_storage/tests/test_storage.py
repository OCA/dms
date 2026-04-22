# Copyright 2020 Creu Blanca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64
import uuid

from odoo.tests import Form, tagged
from odoo.tools import human_size, mute_logger

from odoo.addons.fs_storage.tests.common import TestFSStorageCase


@tagged("post_install", "-at_install")
class TestDmsField(TestFSStorageCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.access_group = cls.env["dms.access.group"].create(
            {
                "name": "Access Group",
                "group_ids": [(4, cls.env.ref("base.group_user").id)],
            }
        )
        cls.storage = cls.env["dms.storage"].create(
            {
                "name": "DMS Storage",
                "save_type": "storage",
                "storage_backend_id": cls.backend.id,
            }
        )
        cls.storage_database = cls.env["dms.storage"].create(
            {
                "name": "DMS Database",
                "save_type": "database",
            }
        )
        cls.directory = cls.env["dms.directory"].create(
            {"storage_id": cls.storage.id, "is_root_directory": True, "name": "MY DIR"}
        )
        cls.directory_database = cls.env["dms.directory"].create(
            {
                "storage_id": cls.storage_database.id,
                "is_root_directory": True,
                "name": "MY DIR",
            }
        )

    @classmethod
    def content_base64(cls):
        return base64.b64encode(b"\xff data")

    @classmethod
    @mute_logger("py.warnings")
    def create_file(cls, directory, content=False, sudo=False):
        model = cls.env["dms.file"].sudo() if sudo else cls.env["dms.file"]
        record = Form(model)
        record.name = uuid.uuid4().hex
        record.directory_id = directory
        record.content = content or cls.content_base64()
        return record.save()

    @mute_logger("py.warnings")
    def test_storage_file_migration(self):
        file = self.create_file(self.directory)
        self.assertTrue(file.storage_backend_id)
        self.assertTrue(file.storage_path)
        path = file.storage_path.rsplit("/", 1)[0]
        self.assertTrue(self.backend.list_files(path))
        file.directory_id = self.directory_database
        self.assertTrue(file.storage_backend_id)
        file.action_migrate()
        self.assertFalse(file.storage_backend_id)
        self.assertFalse(file.storage_path)

    @mute_logger("py.warnings")
    def test_storage_file_move(self):
        file = self.create_file(self.directory)
        self.assertTrue(file.storage_backend_id)
        self.assertTrue(file.storage_path)
        path = file.storage_path
        self.assertEqual(
            self.content_base64(), base64.b64encode(self.backend.get(path))
        )
        file.name = uuid.uuid4()
        file.write({"content": self.content_base64()})
        with self.assertRaises(FileNotFoundError):
            self.backend.get(path)
        self.assertEqual(
            human_size(len(base64.b64decode(self.content_base64()))),
            file.with_context(bin_size=True).content.decode("utf-8"),
        )
