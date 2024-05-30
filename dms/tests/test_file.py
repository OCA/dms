# Copyright 2017-2019 MuK IT GmbH.
# Copyright 2020 Creu Blanca
# Copyright 2021-2022 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64

from odoo.exceptions import UserError
from odoo.tests import new_test_user
from odoo.tests.common import users
from odoo.tools import mute_logger

from .common import StorageFileBaseCase

try:
    import magic
except ImportError:
    magic = None


class FileFilestoreTestCase(StorageFileBaseCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_a = new_test_user(cls.env, login="user-a", groups="dms.group_dms_user")
        cls.directory_group_a = cls.create_directory(storage=cls.storage)
        cls.inaccessible_directory = cls.create_directory(storage=cls.storage)
        cls.inaccessible_file = cls.create_file(directory=cls.inaccessible_directory)
        cls.inaccessible_group = cls.access_group_model.create(
            {
                "name": "Inaccessible Group. No directory set",
                "perm_create": True,
                "explicit_user_ids": [(6, 0, [cls.user_a.id])],
            }
        )
        cls.sub_directory_x = cls.create_directory(directory=cls.directory_group_a)
        cls.group_a = cls.access_group_model.create(
            {
                "name": "Group A",
                "perm_create": True,
                "explicit_user_ids": [(6, 0, [cls.user_a.id])],
                "directory_ids": [
                    (4, cls.directory_group_a.id),
                    (4, cls.sub_directory_x.id),
                ],
            }
        )
        cls.directory_group_a.group_ids = [(4, cls.group_a.id)]
        cls.file2 = cls.create_file(directory=cls.sub_directory_x)

    @users("user-a")
    def test_unaccessible_file(self):
        dms_files = self.file_model.with_user(self.env.user).search(
            [("storage_id", "=", self.storage.id)]
        )
        self.assertNotIn(
            self.inaccessible_file.id,
            dms_files.ids,
            msg="User A should not see the unaccessible file since it "
            "was not granted access to the directory",
        )
        self.assertIn(
            self.file2.id,
            dms_files.ids,
            msg="User A should see the file2 since it was granted access to "
            "the directory",
        )

    @users("user-a")
    def test_inaccessible_directory(self):
        dms_directories = self.directory_model.with_user(self.env.user).search(
            [("storage_id", "=", self.storage.id)]
        )
        self.assertNotIn(
            self.inaccessible_directory.id,
            dms_directories.ids,
            msg="User A should not see the inaccessible directory since "
            "it was not granted access to the directory",
        )
        self.assertIn(
            self.sub_directory_x.id,
            dms_directories.ids,
            msg="User A should see the sub_directory_x since it was granted "
            "access to the directory",
        )

    @users("user-a")
    def test_file_access(self):
        dms_files = self.file_model.with_user(self.env.user).search(
            [("storage_id", "=", self.storage.id)]
        )
        self.assertNotIn(self.file.id, dms_files.ids, msg="User A should not see file")
        self.assertIn(self.file2.id, dms_files.ids, msg="User A should see file2")
        dms_directories = self.directory_model.with_user(self.env.user).search(
            [("storage_id", "=", self.storage.id)]
        )
        self.assertNotIn(
            self.directory.id,
            dms_directories.ids,
            msg="User A should not see directory",
        )
        self.assertIn(
            self.sub_directory_x.id,
            dms_directories.ids,
            msg="User A should see sub_directory_x",
        )

    @users("dms-manager", "dms-user")
    @mute_logger("odoo.models.unlink")
    def test_content_file(self):
        object_file = self.create_file(directory=self.directory)
        self.assertTrue(object_file.content, msg="Content is not empty")
        self.assertTrue(object_file.content_file, msg="Content file is not empty")
        self.assertTrue(
            object_file.with_context(bin_size=True).content,
            msg="Content is not empty (with bin_size)",
        )
        self.assertTrue(
            object_file.with_context(bin_size=True).content_file,
            msg="Content file is not empty (with bin_size)",
        )
        self.assertTrue(
            object_file.with_context(human_size=True).content_file,
            msg="Content file is not empty (with human_size)",
        )
        self.assertTrue(
            object_file.with_context(base64=True).content_file,
            msg="Content file is not empty (with base64)",
        )
        self.assertTrue(
            object_file.with_context(stream=True).content_file,
            msg="Content file is not empty (with stream)",
        )
        oid = object_file.with_context(oid=True).content_file
        self.assertTrue(oid, msg="Content file is not empty (with oid)")
        object_file.with_context(**{"show_content": True}).write(
            {"content": base64.b64encode(b"\xff new content")}
        )
        self.assertNotEqual(
            oid,
            object_file.with_context(**{"oid": True}).content_file,
            msg="Content file has changed",
        )
        self.assertTrue(object_file.export_data(["content"]))
        object_file.unlink()

    def test_content_file_mimetype(self):
        file_svg = self.env.ref("dms.file_05_demo")
        self.assertEqual(file_svg.mimetype, "image/svg+xml", msg="SVG mimetype")
        file_logo = self.env.ref("dms.file_02_demo")
        self.assertEqual(file_logo.mimetype, "image/jpeg", msg="JPEG mimetype")

    def test_content_file_mimetype_magic_library(self):
        if not magic:
            self.skipTest("Without python-magic library installed")
        file_video = self.env.ref("dms.file_10_demo")
        self.assertEqual(file_video.mimetype, "video/mp4", msg="MP4 mimetype")

    def test_content_file_extension(self):
        file_pdf = self.env.ref("dms.file_27_demo")
        self.assertEqual(file_pdf.extension, "pdf", msg="PDF extension")
        file_pdf.name = "Document_05"
        self.assertEqual(
            file_pdf.extension, "pdf", msg="PDF extension without extension"
        )
        file_pdf.name = "Document_05.pdf"
        self.assertEqual(file_pdf.extension, "pdf", msg="PDF extension with extension")

    def test_wizard_dms_file_move(self):
        file3 = self.create_file(directory=self.sub_directory_x)
        all_files = self.file + self.file2 + file3
        # Error: All files must have the same root directory
        with self.assertRaises(
            UserError, msg="All files must have the same root directory"
        ):
            self.file_model.with_context(
                active_ids=all_files.ids
            ).action_wizard_dms_file_move()
        # Change the files that have the same root directory
        files = self.file2 + file3
        res = self.file_model.with_context(
            active_ids=files.ids
        ).action_wizard_dms_file_move()
        wizard_model = self.env[res["res_model"]].with_context(**res["context"])
        wizard = wizard_model.create({"directory_id": self.directory.id})
        self.assertEqual(wizard.count_files, 2, msg="Wizard has 2 files")
        wizard.process()
        self.assertEqual(
            self.file2.directory_id, self.directory, msg="File2 has a new directory"
        )
        self.assertEqual(
            file3.directory_id, self.directory, msg="File3 has a new directory"
        )
