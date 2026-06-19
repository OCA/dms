# Copyright 2026 ledoent — Don Kendall
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64
import logging
import os
import subprocess
import tempfile

from odoo import models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# Mimetypes this module knows how to convert. Mirrors the OFFICE_MIMETYPES
# set in dms/static/src/js/components/preview/handlers.esm.js so the JS
# handler's match() predicate stays in lockstep with what the server can
# actually deliver. If you add a mimetype here, add it there too.
OFFICE_MIMETYPES = frozenset(
    {
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.oasis.opendocument.text",
        "application/rtf",
        # libmagic detects RTF as text/rtf, not application/rtf — without
        # this, RTF files match TextPreview (text/*) at score 0 and render
        # as raw RTF source markup instead of routing through soffice.
        "text/rtf",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.oasis.opendocument.spreadsheet",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/vnd.oasis.opendocument.presentation",
    }
)

# Office extensions, used as a fallback when the stored mimetype is generic.
# libmagic records several office docs (notably the OCA demo's Document_04.rtf)
# as text/plain or application/octet-stream; the base dms preview pane already
# remaps those to an office mimetype off the extension before routing here, so
# the support check has to honour the extension too — otherwise the JS handler
# points the iframe at our route and the server 404s it. Keep aligned with
# OFFICE_MIMETYPES above.
_OFFICE_EXTENSIONS = frozenset(
    {"doc", "docx", "odt", "rtf", "xls", "xlsx", "ods", "ppt", "pptx", "odp"}
)

# Prefix on ir.attachment.description that we use as a cache key. The value
# after the colon is the dms.file.write_date at conversion time; a mismatch
# between the cached value and the current write_date means the source has
# been updated and we need to re-convert.
_CACHE_DESCRIPTION_PREFIX = "libreoffice_preview:"

# Hard cap on soffice runtime. Most real documents convert in <5s; a 60s
# ceiling stops a single hung file from blocking an Odoo worker indefinitely.
_CONVERT_TIMEOUT = 60


class DmsFile(models.Model):
    _inherit = "dms.file"

    def _libreoffice_preview_supported(self):
        """True when we can hand this file to soffice for a PDF preview.

        Stored mimetype first, then an extension fallback: a generic stored
        type (libmagic logs some office docs as text/plain) would 404 the
        route even though the JS handler routed here off the extension. The
        fallback keeps the two in lockstep so mis-typed files still preview.
        """
        self.ensure_one()
        if self.mimetype in OFFICE_MIMETYPES:
            return True
        return (self.extension or "").lstrip(".").lower() in _OFFICE_EXTENSIONS

    def _libreoffice_preview_attachment(self):
        """Return the cached preview ir.attachment, or an empty recordset.

        Cache validity is keyed on `dms.file.checksum` (SHA1 of content,
        already maintained by base dms). This is intentionally NOT keyed
        on `write_date` — renaming a file should not force re-conversion,
        only content edits should.
        """
        self.ensure_one()
        if not self.checksum:
            return self.env["ir.attachment"]
        expected = _CACHE_DESCRIPTION_PREFIX + self.checksum
        return self.env["ir.attachment"].search(
            [
                ("res_model", "=", "dms.file"),
                ("res_id", "=", self.id),
                ("description", "=", expected),
                ("mimetype", "=", "application/pdf"),
            ],
            limit=1,
        )

    def _ensure_libreoffice_preview(self):
        """Return a cached or freshly-converted PDF ir.attachment.

        Raises `UserError` if the source mimetype isn't in our convertible
        set — callers are expected to gate on `_libreoffice_preview_supported`
        before invoking this. Bypasses ACL checks intentionally: it is the
        controller's job to enforce access, this method just does the work.
        """
        self.ensure_one()
        if not self._libreoffice_preview_supported():
            raise UserError(
                self.env._(
                    "%s is not an office format this module can convert.", self.name
                )
            )

        cached = self._libreoffice_preview_attachment()
        if cached:
            return cached

        pdf_bytes = self._convert_with_libreoffice()
        return self.env["ir.attachment"].create(
            {
                "name": (self.name or "file") + ".preview.pdf",
                "res_model": "dms.file",
                "res_id": self.id,
                "mimetype": "application/pdf",
                "datas": base64.b64encode(pdf_bytes),
                "description": _CACHE_DESCRIPTION_PREFIX + (self.checksum or ""),
            }
        )

    def _convert_with_libreoffice(self):
        """Run `soffice --headless --convert-to pdf` and return PDF bytes.

        Each call gets its own temp directory so concurrent conversions
        don't collide on `.~lock.<file>#` markers. Source extension is
        preserved on the temp file because LibreOffice infers the input
        format from the extension (not from sniffing the content).
        """
        self.ensure_one()
        source_bytes = base64.b64decode(self.content or b"")
        if not source_bytes:
            raise UserError(self.env._("%s has no content to convert.", self.name))

        suffix = "." + (self.extension or "").lstrip(".") if self.extension else ""
        with tempfile.TemporaryDirectory(prefix="dms_libreoffice_") as workdir:
            src_path = os.path.join(workdir, "source" + suffix)
            with open(src_path, "wb") as fh:
                fh.write(source_bytes)
            try:
                subprocess.run(
                    [
                        "soffice",
                        "--headless",
                        "--convert-to",
                        "pdf",
                        "--outdir",
                        workdir,
                        src_path,
                    ],
                    capture_output=True,
                    check=True,
                    timeout=_CONVERT_TIMEOUT,
                )
            except FileNotFoundError as e:
                # `soffice` not on $PATH — apt packages were not installed.
                raise UserError(
                    self.env._(
                        "LibreOffice (soffice) is not installed on the server. "
                        "Install libreoffice + fonts-noto + fonts-liberation, or "
                        "remove the dms_libreoffice_preview module."
                    )
                ) from e
            except subprocess.TimeoutExpired as e:
                raise UserError(
                    self.env._(
                        "LibreOffice conversion of %(name)s timed out after "
                        "%(timeout)ss. Source may be malformed or unusually large.",
                        name=self.name,
                        timeout=_CONVERT_TIMEOUT,
                    )
                ) from e
            except subprocess.CalledProcessError as e:
                _logger.warning(
                    "soffice failed for dms.file id=%s: stderr=%s",
                    self.id,
                    (e.stderr or b"").decode("utf-8", errors="replace")[:500],
                )
                raise UserError(
                    self.env._(
                        "LibreOffice could not convert %s. Source may be corrupted.",
                        self.name,
                    )
                ) from e

            pdf_path = os.path.join(workdir, "source.pdf")
            if not os.path.exists(pdf_path):
                raise UserError(
                    self.env._("LibreOffice produced no output for %s.", self.name)
                )
            with open(pdf_path, "rb") as fh:
                return fh.read()
