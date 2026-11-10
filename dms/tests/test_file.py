# Copyright 2017-2019 MuK IT GmbH.
# Copyright 2020 Creu Blanca
# Copyright 2021-2022 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64

from odoo.exceptions import AccessError, UserError
from odoo.tests import new_test_user
from odoo.tests.common import users
from odoo.tools import mute_logger

from .common import StorageFileBaseCase, read_test_asset

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

    @users("user-a")
    @mute_logger("odoo.addons.base.models.ir_access", "odoo.models")
    def test_record_level_access(self):
        """Record-level access for the DMS access-group path: user-a is
        granted on ``directory_group_a`` / ``sub_directory_x`` but not on the
        inaccessible directory/file. Exercises ``check_access`` (read/write/
        unlink) and a real ``create`` on both the allowed and denied side."""
        # Include: granted records are reachable, and create is allowed where
        # the access group grants it.
        self.file2.with_user(self.env.user).check_access("read")
        self.sub_directory_x.with_user(self.env.user).check_access("read")
        self.file_model.with_user(self.env.user).create(
            {
                "name": "user-a allowed",
                "directory_id": self.directory_group_a.id,
                "content": self.content_base64(),
            }
        )
        # Exclude: ungranted records raise for read/write/unlink...
        forbidden_file = self.inaccessible_file.with_user(self.env.user)
        for operation in ("read", "write", "unlink"):
            with self.assertRaises(
                AccessError, msg=f"user-a {operation} must be denied"
            ):
                forbidden_file.check_access(operation)
        # ...and creating in an ungranted directory is denied.
        with self.assertRaises(AccessError, msg="user-a create must be denied"):
            self.file_model.with_user(self.env.user).create(
                {
                    "name": "user-a denied",
                    "directory_id": self.inaccessible_directory.id,
                    "content": self.content_base64(),
                }
            )

    @users("user-a")
    @mute_logger("odoo.addons.base.models.ir_access")
    def test_read_by_id_denied(self):
        """Reading an ungranted record by id must fail: since 20.0 the ORM
        checks read access in sudo through ``filtered_domain()``, which relies
        on the computed ``permission_*`` fields."""
        forbidden_file = self.inaccessible_file.with_user(self.env.user)
        self.assertFalse(forbidden_file.has_access("read"))
        self.assertFalse(forbidden_file._filtered_access("read"))
        self.assertFalse(forbidden_file.permission_read)
        with self.assertRaises(AccessError):
            forbidden_file.read(["name"])
        allowed_file = self.file2.with_user(self.env.user)
        self.assertTrue(allowed_file.has_access("read"))
        self.assertTrue(allowed_file.permission_read)
        self.assertEqual(allowed_file.read(["name"])[0]["id"], self.file2.id)

    @mute_logger("odoo.addons.base.models.ir_access")
    def test_read_by_id_denied_without_dms_group(self):
        """An internal user without DMS access groups can't read DMS records."""
        dms_file = self.file2.with_user(self.user)
        self.assertFalse(dms_file.has_access("read"))
        with self.assertRaises(AccessError):
            dms_file.read(["name"])
        with self.assertRaises(AccessError):
            self.sub_directory_x.with_user(self.user).read(["name"])

    def test_permissions_refresh_on_group_change(self):
        """Permissions are not field dependencies: they must be refreshed
        when the DMS access groups change in the same transaction."""
        forbidden_file = self.inaccessible_file.with_user(self.user_a)
        self.assertFalse(forbidden_file.permission_read)
        self.assertFalse(forbidden_file.has_access("read"))
        self.inaccessible_directory.group_ids = [(4, self.group_a.id)]
        self.assertTrue(forbidden_file.permission_read)
        self.assertTrue(forbidden_file.has_access("read"))

    @mute_logger("odoo.addons.base.models.ir_access")
    def test_hidden_storage_access(self):
        """Only DMS managers can read hidden storages."""
        self.storage.is_hidden = True
        for user in (self.user, self.dms_user):
            with self.assertRaises(AccessError):
                self.storage.with_user(user).read(["name"])
        self.assertTrue(self.storage.with_user(self.dms_manager_user).name)
        self.storage.is_hidden = False
        self.assertTrue(self.storage.with_user(self.dms_user).name)

    @users("user-a")
    def test_permission_search_polarity(self):
        """A negated permission search must be the complement of the positive
        one: `not in` is dispatched straight to the search method, so the
        domain has to be negated there."""
        domain = [("storage_id", "=", self.storage.id)]
        readable = self.file_model.with_user(self.env.user).search(
            domain + [("permission_read", "=", True)]
        )
        self.assertIn(self.file2.id, readable.ids, msg="Granted file must match")
        unreadable = self.file_model.with_user(self.env.user).search(
            domain + [("permission_read", "=", False)]
        )
        self.assertNotIn(
            self.file2.id,
            unreadable.ids,
            msg="A granted file must never match the complement search",
        )
        self.assertFalse(
            unreadable,
            msg="Read rules already restrict results to readable records, so "
            "the complement search must come back empty",
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
        object_file.with_context(show_content=True).write(
            {"content": base64.b64encode(b"\xff new content").decode()}
        )
        self.assertNotEqual(
            oid,
            object_file.with_context(oid=True).content_file,
            msg="Content file has changed",
        )
        self.assertTrue(object_file.export_data(["content"]))
        object_file.unlink()

    def test_content_file_mimetype(self):
        file_svg = self.create_file(
            directory=self.directory, content=read_test_asset("vector.svg")
        )
        self.assertEqual(file_svg.mimetype, "image/svg+xml", msg="SVG mimetype")
        file_logo = self.create_file(
            directory=self.directory, content=read_test_asset("image02.jpg")
        )
        self.assertEqual(file_logo.mimetype, "image/jpeg", msg="JPEG mimetype")

    def test_content_file_mimetype_magic_library(self):
        if not magic:
            self.skipTest("Without python-magic library installed")
        file_video = self.create_file(
            directory=self.directory, content=read_test_asset("video.mp4")
        )
        self.assertEqual(file_video.mimetype, "video/mp4", msg="MP4 mimetype")

    def test_content_file_extension(self):
        file_pdf = self.create_file(
            directory=self.directory, content=read_test_asset("document01.pdf")
        )
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
