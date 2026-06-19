# Copyright 2026 ledoent — Don Kendall
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64
import io
import shutil
import unittest
import uuid
import zipfile
from unittest import mock

import odoo.tests

from odoo.addons.dms.tests.common import DocumentsBaseCase

_ODT_MIMETYPE = "application/vnd.oasis.opendocument.text"

# Minimal ODT body — just enough for LibreOffice to recognize it as a
# valid OpenDocument Text file. ODT is a zip with a `mimetype` file
# (first entry, STORED) + content.xml + meta.xml. Synthesized in-process
# so the test doesn't ship a binary fixture in the repo.
_ODT_CONTENT_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<office:document-content
    xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
    xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
    office:version="1.2">
  <office:body>
    <office:text>
      <text:p>Hello from dms_libreoffice_preview test fixture.</text:p>
    </office:text>
  </office:body>
</office:document-content>
"""


def _build_minimal_odt(seed=""):
    """Return base64-encoded bytes of a minimal valid ODT document.

    The ZIP must have `mimetype` as the first entry, stored uncompressed,
    with no extra fields — that's the OpenDocument spec requirement for
    magic-byte sniffing. Subsequent entries can be compressed.

    `seed` is an optional string appended to the body so cache-invalidation
    tests can build a second fixture with a different SHA1 checksum.
    """
    content_xml = _ODT_CONTENT_XML.replace(
        b"test fixture.", b"test fixture. seed=" + seed.encode("ascii")
    )
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zi = zipfile.ZipInfo("mimetype")
        zi.compress_type = zipfile.ZIP_STORED
        zf.writestr(zi, _ODT_MIMETYPE)
        zf.writestr("content.xml", content_xml)
        zf.writestr(
            "META-INF/manifest.xml",
            (
                """<?xml version="1.0" encoding="UTF-8"?>
<manifest:manifest
    xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0">
  <manifest:file-entry
      manifest:full-path="/" manifest:media-type=\""""
                + _ODT_MIMETYPE
                + """\"/>
  <manifest:file-entry
      manifest:full-path="content.xml" manifest:media-type="text/xml"/>
</manifest:manifest>
"""
            ).encode("utf-8"),
        )
    return base64.b64encode(buf.getvalue())


class _CommonPreview(DocumentsBaseCase):
    """Bring up a storage + directory + .odt file once for the suite."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.storage = cls.create_storage(save_type="database")
        cls.directory = cls.create_directory(storage=cls.storage)
        cls.odt_file = cls.create_file(
            directory=cls.directory, content=_build_minimal_odt()
        )
        cls.odt_file.invalidate_recordset()
        # `dms-user` is in `cls.access_group` (per DocumentsBaseCase) and
        # therefore allowed to read files in cls.directory. Admin is NOT
        # in that group, so HttpCase tests authenticate as this user.
        # new_test_user() doesn't set a password by default — set it here
        # so HttpCase.authenticate() can log in.
        cls.dms_user.password = "dms-user"

    @classmethod
    def _have_soffice(cls):
        return shutil.which("soffice") is not None


class TestLibreofficePreview(_CommonPreview):
    def test_supported_mimetype_predicate(self):
        """ODT mimetype is reported as supported; arbitrary bytes are not."""
        self.assertEqual(self.odt_file.mimetype, _ODT_MIMETYPE)
        self.assertTrue(self.odt_file._libreoffice_preview_supported())

        plain = self.create_file(
            directory=self.directory, content=base64.b64encode(b"plain text bytes")
        )
        plain.invalidate_recordset()
        self.assertFalse(plain._libreoffice_preview_supported())

    def test_convert_happy_path(self):
        """soffice produces a PDF and we cache it as an ir.attachment."""
        if not self._have_soffice():
            raise unittest.SkipTest("soffice not installed on this runner")
        att = self.odt_file._ensure_libreoffice_preview()
        self.assertEqual(att.mimetype, "application/pdf")
        self.assertEqual(att.res_model, "dms.file")
        self.assertEqual(att.res_id, self.odt_file.id)
        self.assertTrue(base64.b64decode(att.datas).startswith(b"%PDF-"))

    def test_cache_hit_returns_same_attachment(self):
        """Second call returns the same row — no extra ir.attachment created."""
        if not self._have_soffice():
            raise unittest.SkipTest("soffice not installed on this runner")
        first = self.odt_file._ensure_libreoffice_preview()
        second = self.odt_file._ensure_libreoffice_preview()
        self.assertEqual(first.id, second.id)

    def test_cache_invalidation_on_content_change(self):
        """Replacing the source content forces a new conversion.

        Cache is keyed on `dms.file.checksum` (SHA1 of content), so a
        rename alone does NOT trigger re-conversion — only an actual
        content change does. We swap in a fresh ODT body here to make
        sure the checksum drifts.
        """
        if not self._have_soffice():
            raise unittest.SkipTest("soffice not installed on this runner")
        first = self.odt_file._ensure_libreoffice_preview()
        first_checksum = self.odt_file.checksum
        # Different body → different checksum → cache miss on next call.
        self.odt_file.write({"content": _build_minimal_odt(seed=uuid.uuid4().hex)})
        self.odt_file.invalidate_recordset()
        self.assertNotEqual(first_checksum, self.odt_file.checksum)
        second = self.odt_file._ensure_libreoffice_preview()
        self.assertNotEqual(first.id, second.id)

    def test_soffice_not_installed_raises_useful_error(self):
        """FileNotFoundError → UserError with install hint, no leaked traces."""
        from odoo.exceptions import UserError

        with mock.patch(
            "odoo.addons.dms_libreoffice_preview.models.dms_file.subprocess.run",
            side_effect=FileNotFoundError(),
        ):
            with self.assertRaises(UserError) as cm:
                self.odt_file._convert_with_libreoffice()
            self.assertIn("LibreOffice", str(cm.exception))


@odoo.tests.tagged("post_install", "-at_install")
class TestLibreofficePreviewHttp(odoo.tests.HttpCase, _CommonPreview):
    def test_controller_404_when_not_supported(self):
        """A non-office file → 404 from the controller (don't expose existence)."""
        plain = self.create_file(
            directory=self.directory, content=base64.b64encode(b"x")
        )
        plain.invalidate_recordset()
        # `dms-user` is the user in the test access group; admin is NOT,
        # so authenticating as admin would 404 the test for the wrong reason.
        self.authenticate("dms-user", "dms-user")
        r = self.url_open(f"/dms/file/{plain.id}/libreoffice_preview", timeout=20)
        self.assertEqual(r.status_code, 404)

    def test_controller_returns_pdf(self):
        """Office file → 200 + application/pdf payload."""
        if not self._have_soffice():
            raise unittest.SkipTest("soffice not installed on this runner")
        self.authenticate("dms-user", "dms-user")
        r = self.url_open(
            f"/dms/file/{self.odt_file.id}/libreoffice_preview", timeout=60
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers.get("Content-Type", ""), "application/pdf")
        self.assertTrue(r.content.startswith(b"%PDF-"))
