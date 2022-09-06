# Copyright 2017-2019 MuK IT GmbH.
# Copyright 2020 Creu Blanca
# Copyright 2021-2022 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64

from odoo.tests import new_test_user
from odoo.tests.common import users

from .common import StorageFileBaseCase

try:
    import magic
except ImportError:
    magic = None


class FileFilestoreTestCase(StorageFileBaseCase):
    def setUp(self):
        super().setUp()
        self.user_a = new_test_user(
            self.env, login="user-a", groups="dms.group_dms_user"
        )
        self.group_a = self.access_group_model.create(
            {
                "name": "Group A",
                "perm_create": True,
                "explicit_user_ids": [(6, 0, [self.user_a.id])],
            }
        )
        self.directory_group_a = self.create_directory(storage=self.storage)
        self.directory_group_a.group_ids = [(4, self.group_a.id)]
        self.sub_directory_x = self.create_directory(directory=self.directory_group_a)
        self.file2 = self.create_file(directory=self.sub_directory_x)

    @users("user-a")
    def test_file_access(self):
        dms_files = self.file_model.with_user(self.env.user).search(
            [("storage_id", "=", self.storage.id)]
        )
        self.assertNotIn(self.file.id, dms_files.ids)
        self.assertIn(self.file2.id, dms_files.ids)
        dms_directories = self.directory_model.with_user(self.env.user).search(
            [("storage_id", "=", self.storage.id)]
        )
        self.assertNotIn(self.directory.id, dms_directories.ids)
        self.assertIn(self.sub_directory_x.id, dms_directories.ids)

    @users("dms-manager", "dms-user")
    def test_content_file(self):
        lobject_file = self.create_file(directory=self.directory)
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

    def test_content_file_mimetype(self):
        file_svg = self.env.ref("dms.file_05_demo")
        self.assertEqual(file_svg.mimetype, "image/svg+xml")
        file_logo = self.env.ref("dms.file_02_demo")
        self.assertEqual(file_logo.mimetype, "image/jpeg")

    def test_content_file_mimetype_magic_library(self):
        if not magic:
            self.skipTest("Without python-magic library installed")
        file_video = self.env.ref("dms.file_10_demo")
        self.assertEqual(file_video.mimetype, "video/mp4")

    def test_content_file_extension(self):
        file_pdf = self.env.ref("dms.file_27_demo")
        self.assertEqual(file_pdf.extension, "pdf")
        file_pdf.name = "Document_05"
        self.assertEqual(file_pdf.extension, "pdf")
        file_pdf.name = "Document_05.pdf"
        self.assertEqual(file_pdf.extension, "pdf")
