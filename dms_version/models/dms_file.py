# Copyright 2017-2020 MuK IT GmbH
# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class DmsFile(models.Model):
    _name = "dms.file"
    _inherit = ["dms.file", "base.revision"]

    current_revision_id = fields.Many2one(
        comodel_name="dms.file",
    )
    old_revision_ids = fields.One2many(
        comodel_name="dms.file",
    )
    has_versioning = fields.Boolean(
        related="storage_id.has_versioning",
    )

    _sql_constraints = [
        (
            "revision_unique",
            "unique(unrevisioned_name, revision_number, has_versioning)",
            "Reference and revision must be unique in vesioning.",
        )
    ]

    def action_view_revision(self):
        self.ensure_one()
        action = self.env.ref("dms_version.action_dms_revisions_file")
        return action.read()[0]

    def write(self, vals):
        res = super().write(vals)
        if vals.get("content"):
            self.filtered(lambda x: x.storage_id.has_versioning).create_revision()
        return res
