# Copyright 2026 Ledo Enterprises
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import json
import logging

from odoo import api, fields, models
from odoo.exceptions import AccessError

_logger = logging.getLogger(__name__)

SPREADSHEET_MIMETYPE = "application/o-spreadsheet"


class DmsFile(models.Model):
    _name = "dms.file"
    _inherit = ["dms.file", "spreadsheet.abstract"]

    handler = fields.Selection(
        selection=[("spreadsheet", "Spreadsheet")],
        index=True,
    )

    # ── Lifecycle ────────────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("mimetype") == SPREADSHEET_MIMETYPE:
                vals["handler"] = "spreadsheet"
                if vals.get("content") and not vals.get("spreadsheet_binary_data"):
                    vals["spreadsheet_binary_data"] = vals["content"]
        return super().create(vals_list)

    def write(self, vals):
        if vals.get("mimetype") == SPREADSHEET_MIMETYPE:
            vals["handler"] = "spreadsheet"
        return super().write(vals)

    # ── Storage bridge ───────────────────────────────────────────────────────

    def _compute_content(self):
        """For spreadsheet files, content mirrors spreadsheet_binary_data."""
        spreadsheets = self.filtered(lambda f: f.handler == "spreadsheet")
        for rec in spreadsheets:
            rec.content = rec.spreadsheet_binary_data
        return super(DmsFile, self - spreadsheets)._compute_content()

    def _inverse_content(self):
        """For spreadsheet files, write-through to spreadsheet_binary_data."""
        spreadsheets = self.filtered(lambda f: f.handler == "spreadsheet")
        for rec in spreadsheets:
            rec.spreadsheet_binary_data = rec.content
        return super(DmsFile, self - spreadsheets)._inverse_content()

    # ── spreadsheet.abstract interface ───────────────────────────────────────

    def get_spreadsheet_data(self):
        """Return data payload consumed by action_spreadsheet_oca client action."""
        self.ensure_one()
        mode = "normal"
        try:
            self.check_access("write")
        except AccessError:
            mode = "readonly"

        raw = {}
        if self.spreadsheet_binary_data:
            try:
                raw = json.loads(
                    base64.decodebytes(self.spreadsheet_binary_data).decode("utf-8")
                )
            except (ValueError, UnicodeDecodeError):
                _logger.warning(
                    "Could not decode spreadsheet data for dms.file %s", self.id
                )

        revisions = []
        for rev in self.spreadsheet_revision_ids:
            try:
                revisions.append(
                    dict(
                        json.loads(rev.commands),
                        nextRevisionId=rev.next_revision_id,
                        serverRevisionId=rev.server_revision_id,
                    )
                )
            except (ValueError, UnicodeDecodeError):
                _logger.warning(
                    "Skipping malformed revision %s on dms.file %s", rev.id, self.id
                )

        return {
            "name": self.name,
            "spreadsheet_raw": raw,
            "revisions": revisions,
            "mode": mode,
            "default_currency": self.env[
                "res.currency"
            ].get_company_currency_for_spreadsheet(),
            "user_locale": self.env["res.lang"]._get_user_spreadsheet_locale(),
        }

    def open_spreadsheet(self):
        self.ensure_one()
        return {
            "type": "ir.actions.client",
            "tag": "action_spreadsheet_oca",
            "params": {"spreadsheet_id": self.id, "model": self._name},
        }

    @api.model
    def action_open_new_spreadsheet(self):
        """Open the New Spreadsheet wizard, pre-filling directory from context.

        Called from the server action bound to the file kanban/list views so
        that 'New Spreadsheet' appears in the Files ⚙ action menu.
        """
        ctx = self.env.context
        directory_id = ctx.get("default_directory_id") or ctx.get("active_id")
        return {
            "type": "ir.actions.act_window",
            "res_model": "dms.spreadsheet.create",
            "view_mode": "form",
            "target": "new",
            "context": {"default_directory_id": directory_id},
        }

    # ── Computed helpers ─────────────────────────────────────────────────────

    @api.depends("handler")
    def _compute_extension(self):
        """Spreadsheet files use 'oss' extension (MIME not in Python stdlib)."""
        spreadsheets = self.filtered(lambda f: f.handler == "spreadsheet")
        for rec in spreadsheets:
            rec.extension = "oss"
        return super(DmsFile, self - spreadsheets)._compute_extension()

    @api.depends("handler")
    def _compute_mimetype(self):
        spreadsheets = self.filtered(lambda f: f.handler == "spreadsheet")
        for rec in spreadsheets:
            rec.mimetype = SPREADSHEET_MIMETYPE
        return super(DmsFile, self - spreadsheets)._compute_mimetype()
