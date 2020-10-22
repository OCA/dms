# Copyright 2017-2020 MuK IT GmbH
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64
import logging
import zlib
from collections import defaultdict

from odoo import _, api, fields, models, tools
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

import bsdiff4


class FileVersion(models.Model):

    _name = "dms.version"
    _description = "Version"

    _order = "create_date desc"

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

    compress_versions = fields.Boolean(
        related="storage_id.compress_versions", readonly=True
    )

    incremental_versions = fields.Boolean(
        related="storage_id.incremental_versions", readonly=True
    )

    previous_version_id = fields.Many2one(
        comodel_name="dms.version", ondelete="set null", string="Previous Version"
    )

    next_version_id = fields.Many2one(
        comodel_name="dms.version", ondelete="set null", string="Next Version"
    )

    is_compress = fields.Boolean(string="Compressed", default=False)

    is_incremental = fields.Boolean(string="Incremental", default=False)

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

    def get_binary(self, patch=True):
        self.ensure_one()
        binary = base64.b64decode(self.binary)
        if self.is_compress:
            binary = zlib.decompress(binary)
        if self.is_incremental and patch:
            prev_version = self.previous_version_id
            prev_binary = prev_version.get_binary()
            binary = bsdiff4.patch(prev_binary, binary)
        return binary

    @api.model
    def clean_versions(self, files, max_size=None):
        for file in files.filtered(lambda rec: rec.count_versions > 0):
            max_size = max_size or file.storage_id.stored_versions
            if file.count_versions > max_size:
                remove_size = file.count_versions - max_size
                remove_versions = self.env["dms.version"]
                current = file.version_ids.filtered(
                    lambda rec: not rec.previous_version_id
                )
                while len(remove_versions) < remove_size:
                    remove_versions |= current
                    current = current.next_version_id
                current.write(
                    {
                        "content": current.content,
                        "previous_version_id": None,
                        "is_incremental": False,
                    }
                )
                remove_versions.unlink()

    @api.model
    def add_version(self, file, content):
        domain = [
            ("file_id", "=", file.id),
        ]
        record = self.search(domain, order='id desc', limit=1)
        if not record:
            return self.create(
                {"name": file.name, "file_id": file.id, "content": content}
            )
        else:        
            new_version = self.create(
                {
                    "name": file.name,
                    "file_id": file.id,
                    "content": content,
                    "previous_version_id": record.id,
                }
            )
            record.write({"next_version_id": new_version.id})
            return new_version

    @api.model
    def pop_version(self, file):
        domain = [
            ("file_id", "=", file.id),
            ("next_version_id", "=", False),
        ]
        record = self.search(domain, limit=1)
        if not record:
            return (None, None)
        result = (record.name, record.content)
        record.unlink()
        return result

    @api.depends("binary")
    def _compute_content(self):
        bin_size = self.env.context.get("bin_size", False)
        for record in self:
            if bin_size:
                record.content = record.binary
            else:
                binary = record.get_binary() or b""
                record.content = base64.b64encode(binary)

    @api.constrains("previous_version_id", "is_incremental")
    def _check_incremental(self):
        for record in self:
            if record.is_incremental and not record.previous_version_id.exists():
                raise ValidationError(
                    _("An incremental version has to have a previous version.")
                )

    def _inverse_content(self):
        updates = defaultdict(set)
        for record in self:
            is_compress = False
            is_incremental = False
            binary = base64.b64decode(record.content or "")
            if record.incremental_versions and record.previous_version_id.exists():
                prev_binary = record.previous_version_id.get_binary()
                binary = bsdiff4.diff(prev_binary, binary)
                is_incremental = True
            if record.compress_versions:
                binary = zlib.compress(binary, zlib.Z_BEST_COMPRESSION)
                is_compress = True
            values = {
                "binary": base64.b64encode(binary),
                "size": binary and len(binary) or 0,
                "is_incremental": is_incremental,
                "is_compress": is_compress,
            }
            updates[tools.frozendict(values)].add(record.id)
        with self.env.norecompute():
            for vals, ids in updates.items():
                self.browse(ids).write(dict(vals))
        self.recompute()
