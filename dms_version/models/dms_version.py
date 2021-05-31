# Copyright 2017-2020 MuK IT GmbH
# Copyright 2021 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64
from collections import defaultdict

from odoo import api, fields, models, tools


class DmsVersion(models.Model):
    _name = "dms.version"
    _description = "DMS Version"
    _order = "create_date desc"
    _inherit = [
        "dms.security.mixin",
    ]
    _directory_field = "file_id"

    name = fields.Char(string="Name", readonly=True)
    file_id = fields.Many2one(
        comodel_name="dms.file", ondelete="cascade", string="File", required=True
    )
    storage_id = fields.Many2one(
        related="file_id.storage_id",
        comodel_name="dms.storage",
        string="Storage",
        readonly=True,
    )
    previous_version = fields.Many2one(
        comodel_name="dms.version", ondelete="set null", string="Previous Version"
    )
    next_version = fields.Many2one(
        comodel_name="dms.version", ondelete="set null", string="Next Version"
    )
    size = fields.Integer(string="Size", readonly=True)
    content = fields.Binary(
        compute="_compute_content",
        inverse="_inverse_content",
        string="Content",
        attachment=False,
        prefetch=False,
        required=True,
        store=False,
    )
    binary = fields.Binary(
        string="Binary", prefetch=False, attachment=True, invisible=True
    )

    @api.depends("binary")
    @api.depends_context("binary")
    def _compute_content(self):
        bin_size = self.env.context.get("bin_size", False)
        for record in self:
            if bin_size:
                record.content = record.binary
            else:
                binary = base64.b64decode(record.binary) or b""
                record.content = base64.b64encode(binary)

    def _inverse_content(self):
        updates = defaultdict(set)
        for record in self:
            binary = base64.b64decode(record.content or "")
            values = {
                "binary": base64.b64encode(binary),
                "size": binary and len(binary) or 0,
            }
            updates[tools.frozendict(values)].add(record.id)
        with self.env.norecompute():
            for vals, ids in updates.items():
                self.browse(ids).write(dict(vals))
        self.recompute()
