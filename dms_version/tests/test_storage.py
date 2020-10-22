# Copyright 2017-2020 MuK IT GmbH
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging
import os
import unittest

import bsdiff4

from odoo.addons.dms.tests.common import multi_users
from odoo.addons.dms.tests.test_storage import StorageTestCase

_path = os.path.dirname(os.path.dirname(__file__))
_logger = logging.getLogger(__name__)


class StorageVersionTestCase(StorageTestCase):
    def _setup_test_data(self):
        super(StorageVersionTestCase, self)._setup_test_data()
        self.version = self.env["dms.version"]

    @multi_users(
        lambda self: [[self.super_uid, True], [self.admin_uid, True]],
        callback="_setup_test_data",
    )
    def test_version_clean_write(self):
        storage = self.create_storage(sudo=True)
        storage.write(
            {
                "has_versioning": True,
                "clean_versions": "immediately",
                "stored_versions": 3,
            }
        )
        file = self.create_file(storage=storage)
        for _ in range(5):
            file.write({"content": self.content_base64()})
        self.assertTrue(len(file.version_ids.exists()) == 3)
        self.assertTrue(file.count_versions == 3)

    @multi_users(
        lambda self: [[self.super_uid, True], [self.admin_uid, True]],
        callback="_setup_test_data",
    )
    def test_version_clean_autovacuum(self):
        storage = self.create_storage(sudo=True)
        storage.write(
            {
                "has_versioning": True,
                "clean_versions": "autovacuum",
                "stored_versions": 3,
            }
        )
        file = self.create_file(storage=storage)
        for _ in range(5):
            file.write({"content": self.content_base64()})
        self.assertTrue(len(file.version_ids.exists()) == 5)
        self.assertTrue(file.count_versions == 5)
        storage.clean_file_versions()
        self.assertTrue(len(file.version_ids.exists()) == 3)
        self.assertTrue(file.count_versions == 3)

    @multi_users(
        lambda self: [[self.super_uid, True], [self.admin_uid, True]],
        callback="_setup_test_data",
    )
    def test_version_compress(self):
        storage = self.create_storage(sudo=True)
        storage.write(
            {
                "has_versioning": True,
                "clean_versions": "immediately",
                "stored_versions": 3,
                "compress_versions": True,
            }
        )
        file = self.create_file(storage=storage)
        for _ in range(5):
            file.write({"content": self.content_base64()})
        self.assertTrue(len(file.version_ids.exists()) == 3)
        self.assertTrue(all(file.version_ids.mapped("is_compress")))
        self.assertTrue(file.version_ids[0].content == self.content_base64())

    @multi_users(
        lambda self: [[self.super_uid, True], [self.admin_uid, True]],
        callback="_setup_test_data",
    )
    @unittest.skipIf(not bsdiff4, "No bsdiff4 library installed")
    def test_version_incremental(self):
        storage = self.create_storage(sudo=True)
        storage.write({"has_versioning": True, "incremental_versions": True})
        file = self.create_file(storage=storage)
        for _ in range(5):
            file.write({"content": self.content_base64()})
        self.assertTrue(len(file.version_ids.exists()) == 5)
        for version in file.version_ids.exists():
            self.assertTrue(version.content == self.content_base64())

    @multi_users(
        lambda self: [[self.super_uid, True], [self.admin_uid, True]],
        callback="_setup_test_data",
    )
    @unittest.skipIf(not bsdiff4, "No bsdiff4 library installed")
    def test_version_incremental_compress(self):
        storage = self.create_storage(sudo=True)
        storage.write(
            {
                "has_versioning": True,
                "compress_versions": True,
                "incremental_versions": True,
            }
        )
        file = self.create_file(storage=storage)
        for _ in range(5):
            file.write({"content": self.content_base64()})
        self.assertTrue(len(file.version_ids.exists()) == 5)
        for version in file.version_ids.exists():
            self.assertTrue(version.content == self.content_base64())

    @multi_users(
        lambda self: [[self.super_uid, True], [self.admin_uid, True]],
        callback="_setup_test_data",
    )
    @unittest.skipIf(not bsdiff4, "No bsdiff4 library installed")
    def test_version_incremental_clean(self):
        storage = self.create_storage(sudo=True)
        storage.write({"has_versioning": True, "incremental_versions": True})
        file = self.create_file(storage=storage)
        for _ in range(5):
            file.write({"content": self.content_base64()})
        domain = [
            ("file", "=", file.id),
            ("previous_version", "=", False),
        ]
        oldest_version = self.version.search(domain, limit=1)
        newer_versions = file.version_ids - oldest_version
        self.assertTrue(len(file.version_ids.exists()) == 5)
        self.assertFalse(oldest_version.is_incremental)
        self.assertTrue(all(newer_versions.mapped("is_incremental")))
        storage.clean_file_versions()
        new_oldest_version = self.version.search(domain, limit=1)
        newer_versions = file.version_ids.exists() - new_oldest_version
        self.assertTrue(len(file.version_ids.exists()) == 3)
        self.assertTrue(oldest_version != new_oldest_version)
        self.assertFalse(new_oldest_version.is_incremental)
        self.assertTrue(all(newer_versions.mapped("is_incremental")))

    @multi_users(
        lambda self: [[self.super_uid, True], [self.admin_uid, True]],
        callback="_setup_test_data",
    )
    def test_version_delete(self):
        storage = self.create_storage(sudo=True)
        storage.write(
            {
                "has_versioning": True,
                "clean_versions": "immediately",
                "stored_versions": 3,
            }
        )
        file = self.create_file(storage=storage)
        for _ in range(5):
            file.write({"content": self.content_base64()})
        storage.action_delete_file_versions()
        self.assertTrue(len(file.version_ids.exists()) == 0)
        self.assertTrue(file.count_versions == 0)
