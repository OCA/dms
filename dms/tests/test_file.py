# Copyright 2017-2019 MuK IT GmbH.
# Copyright 2020 Creu Blanca
# Copyright 2020 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64

from .test_file_database import FileTestCase


class FileFilestoreTestCase(FileTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.new_storage.with_user(cls.admin_uid).write({"save_type": "file"})

    def test_content_file(self):
        storage = self.create_storage(save_type="file", sudo=True).with_user(
            self.admin_uid
        )
        lobject_file = self.create_file(storage=storage).with_user(self.admin_uid)
        self.assertTrue(lobject_file.content)
        self.assertTrue(lobject_file.content_file)
        self.assertTrue(lobject_file.with_context(bin_size=True).content)
        self.assertTrue(lobject_file.with_context(bin_size=True).content_file)
        self.assertTrue(lobject_file.with_context(human_size=True).content_file)
        self.assertTrue(lobject_file.with_context(base64=True).content_file)
        self.assertTrue(lobject_file.with_context(stream=True).content_file)
        oid = lobject_file.with_context(oid=True).content_file
        self.assertTrue(oid)
        lobject_file.with_context(show_content=True).write(
            {"content": base64.b64encode(b"\xff new content")}
        )
        self.assertNotEqual(oid, lobject_file.with_context({"oid": True}).content_file)
        self.assertTrue(lobject_file.export_data(["content"]))
        lobject_file.unlink()
