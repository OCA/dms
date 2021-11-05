# Copyright 2017-2019 MuK IT GmbH.
# Copyright 2020 Creu Blanca
# Copyright 2021 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64

from .common import multi_users
from .test_file_database import FileTestCase

try:
    import magic
except ImportError:
    magic = None


class FileFilestoreTestCase(FileTestCase):
    def _setup_test_data(self):
        super(FileFilestoreTestCase, self)._setup_test_data()
        self.new_storage.write({"save_type": "file"})

    def test_file_access(self):
        user_a = self.env["res.users"].create(
            {
                "name": "User A",
                "login": "user_a",
                "email": "user_a@user_a.com",
                "groups_id": [
                    (
                        6,
                        0,
                        [
                            self.env.ref("base.group_user").id,
                            self.env.ref("dms.group_dms_user").id,
                        ],
                    )
                ],
            }
        )
        group_a = self.env["dms.access.group"].create(
            {"name": "Group A", "explicit_user_ids": [(6, 0, [user_a.id])]}
        )
        root_directory_a = self.env["dms.directory"].create(
            {
                "name": "Root directory A",
                "is_root_directory": True,
                "storage_id": self.env.ref("dms.storage_demo").id,
                "group_ids": [
                    (6, 0, [self.env.ref("dms.access_group_01_demo").id, group_a.id])
                ],
            }
        )
        sub_directory_x = self.env["dms.directory"].create(
            {
                "name": "Sub directory X",
                "parent_id": root_directory_a.id,
                "inherit_group_ids": True,
            }
        )
        dms_file = self.create_file(directory=sub_directory_x)
        dms_files = self.env["dms.file"].with_user(user_a).search([])
        self.assertTrue(self.env.ref("dms.file_13_demo") not in dms_files)
        self.assertTrue(dms_file in dms_files)
        dms_directories = self.env["dms.directory"].with_user(user_a).search([])
        self.assertTrue(self.env.ref("dms.directory_01_demo") not in dms_directories)
        self.assertTrue(sub_directory_x in dms_directories)

    @multi_users(lambda self: self.multi_users(), callback="_setup_test_data")
    def test_content_file(self):
        storage = self.create_storage(save_type="file", sudo=True)
        lobject_file = self.create_file(storage=storage)
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
