# Copyright 2026 ledoent — Don Kendall
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import http
from odoo.exceptions import AccessError, UserError
from odoo.http import request


class DmsLibreofficePreviewController(http.Controller):
    @http.route(
        "/dms/file/<int:file_id>/libreoffice_preview",
        type="http",
        auth="user",
        methods=["GET"],
        # Not readonly: cache-miss path writes a new ir.attachment via
        # _ensure_libreoffice_preview(). Marking readonly=True triggers
        # Odoo 19's "retry with r/w cursor" warning which checklog-odoo
        # promotes to a build error.
    )
    def libreoffice_preview(self, file_id, **kwargs):
        """Serve a cached or freshly-converted PDF preview inline.

        The `?v=<write_date>` query parameter is not validated server-side
        — it exists purely as a cache-buster for the browser (the iframe
        URL changes when `dms.file.write_date` changes, forcing a refetch
        instead of pulling a stale render from the HTTP cache). Cache
        validity on the server is owned by `_libreoffice_preview_attachment`.
        """
        dms_file = request.env["dms.file"].browse(file_id).exists()
        if not dms_file:
            raise request.not_found()
        try:
            dms_file.check_access("read")
        except AccessError as e:
            raise request.not_found() from e
        if not dms_file._libreoffice_preview_supported():
            raise request.not_found()
        try:
            attachment = dms_file.sudo()._ensure_libreoffice_preview()
        except UserError as e:
            # Conversion errors are surfaced as 502 with the user-facing
            # message — the side-pane handler can render this as an empty
            # state via the existing error path.
            return request.make_response(
                str(e), status=502, headers=[("Content-Type", "text/plain")]
            )
        return (
            request.env["ir.binary"]
            ._get_stream_from(attachment, "raw")
            .get_response(as_attachment=False)
        )
