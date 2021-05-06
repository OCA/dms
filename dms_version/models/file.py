# Copyright 2017-2020 MuK IT GmbH
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class File(models.Model):

    _inherit = "dms.file"

    version_ids = fields.One2many(
        comodel_name="dms.version",
        inverse_name="file_id",
        string="Versions",
        readonly=True,
    )

    count_versions = fields.Integer(
        compute="_compute_count_versions", string="Count Versions"
    )

    @api.model
    def _check_context_no_versioning(self):
        return self.env.context.get("migration") or self.env.context.get("reverting")

    def action_revert_version(self):
        for record in self:
            versions = self.env["dms.version"].sudo()
            content_tuple = versions.pop_version(record)
            record.with_context(reverting=True).write(
                {"content": content_tuple[1], "name": content_tuple[0]}
            )

    def action_delete_versions(self):
        self.mapped("version_ids").sudo().unlink()

    @api.depends("version_ids")
    def _compute_count_versions(self):
        for record in self:
            record.count_versions = len(record.version_ids)

    def write(self, vals):
        if "content" in vals and not self._check_context_no_versioning():
            for record in self.filtered("storage_id.has_versioning"):
                versions = self.env["dms.version"].sudo()
                versions.add_version(record, record.content)
                if record.storage_id.clean_versions == "immediately":
                    versions.clean_versions(record.sudo())
        return super(File, self).write(vals)
