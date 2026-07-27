# Copyright 2026 Millow AB
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
"""Regression tests for share-token scoping.

``dms.file.check_access_token`` used to compare the directory walker against
itself instead of against the directory that owns the token, which made the
whole branch collapse to ``return True``. Any valid directory token therefore
granted read access to *every* file in the database, including files in
unrelated trees and in directories with broken group inheritance.
"""

import uuid

from .common import StorageFileBaseCase


class TestDmsAccessToken(StorageFileBaseCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Two unrelated trees under the same storage.
        #   shared_root / shared_child   <- the token lives on shared_root
        #   other_root                   <- must stay unreachable
        cls.shared_root = cls.create_directory(storage=cls.storage)
        cls.shared_child = cls.create_directory(directory=cls.shared_root)
        cls.other_root = cls.create_directory(storage=cls.storage)

        cls.file_in_shared_root = cls.create_file(directory=cls.shared_root)
        cls.file_in_shared_child = cls.create_file(directory=cls.shared_child)
        cls.file_in_other_root = cls.create_file(directory=cls.other_root)

        cls.token = uuid.uuid4().hex
        cls.shared_root.access_token = cls.token

    # ------------------------------------------------------------------
    # The defect
    # ------------------------------------------------------------------
    def test_token_does_not_grant_access_to_unrelated_tree(self):
        """A token on shared_root must NOT unlock a file under other_root."""
        self.assertFalse(
            self.file_in_other_root.check_access_token(self.token),
            "Directory token leaked into an unrelated directory tree",
        )

    def test_token_does_not_grant_access_to_root_level_file(self):
        """The `# Fix last level` branch self-compared too.

        A file whose directory has no parent skipped the loop entirely and
        fell through to a second always-true comparison, so root-level files
        leaked as well.
        """
        self.assertFalse(
            self.file.check_access_token(self.token),
            "Directory token leaked into a root-level file of another tree",
        )

    def test_unrelated_token_value_is_rejected(self):
        self.assertFalse(
            self.file_in_shared_child.check_access_token(uuid.uuid4().hex),
            "An unknown token value was accepted",
        )

    def test_no_token_is_rejected(self):
        self.assertFalse(self.file_in_shared_child.check_access_token(False))

    # ------------------------------------------------------------------
    # Legitimate behaviour that must keep working
    # ------------------------------------------------------------------
    def test_token_grants_access_to_file_in_the_shared_directory(self):
        self.assertTrue(
            self.file_in_shared_root.check_access_token(self.token),
            "Token did not unlock a file in its own directory",
        )

    def test_token_grants_access_to_file_in_a_descendant_directory(self):
        self.assertTrue(
            self.file_in_shared_child.check_access_token(self.token),
            "Token did not unlock a file in a descendant directory",
        )

    def test_file_own_token_still_works(self):
        own_token = uuid.uuid4().hex
        self.file_in_other_root.access_token = own_token
        self.assertTrue(
            self.file_in_other_root.check_access_token(own_token),
            "A file's own access token stopped working",
        )

    def test_directory_token_grants_access_to_descendant_directory(self):
        """The directory-side implementation was already correct; pin it."""
        self.assertTrue(self.shared_child.check_access_token(self.token))
        self.assertFalse(self.other_root.check_access_token(self.token))
