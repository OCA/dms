# Copyright 2017-2020 MuK IT GmbH
# Copyright 2021 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class DmsFile(models.Model):
    _inherit = "dms.file"

    version_ids = fields.One2many(
        comodel_name="dms.version",
        inverse_name="file_id",
        string="Versions",
        readonly=True,
    )
    versions_count = fields.Integer(compute="_compute_versions_count", store=True)
    storage_id_inherit_access_from_parent_record = fields.Boolean(
        related="storage_id.inherit_access_from_parent_record",
        related_sudo=True,
        auto_join=True,
        store=True,
    )

    @api.depends("version_ids")
    def _compute_versions_count(self):
        for record in self:
            record.versions_count = len(record.version_ids)

    def action_revert_version(self):
        for record in self:
            content_tuple = record._pop_version()
            record.with_context(dms_versioning=True).write(
                {"content": content_tuple[1], "name": content_tuple[0]}
            )

    def action_delete_versions(self):
        self.mapped("version_ids").unlink()

    def write(self, vals):
        if "content" in vals and not self.env.context.get("dms_versioning"):
            for record in self.filtered("storage_id.has_versioning"):
                if not record.require_migration:
                    record._add_version(record.content)
        return super().write(vals)

    def _add_version(self, content):
        dms_version = self.env["dms.version"]
        domain = [
            ("file_id", "=", self.id),
            ("next_version", "=", False),
        ]
        vals = {"name": self.name, "file_id": self.id, "content": content}
        record = dms_version.search(domain, limit=1)
        if not record:
            return dms_version.create(vals)
        vals["previous_version"] = record.id
        new_version = dms_version.create(vals)
        record.write({"next_version": new_version.id})
        return new_version

    def _pop_version(self):
        domain = [
            ("file_id", "=", self.id),
            ("next_version", "=", False),
        ]
        record = self.env["dms.version"].search(domain, limit=1)
        if not record:
            return (None, None)
        result = (record.name, record.content)
        record.unlink()
        return result
