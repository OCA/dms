# Copyright 2017-2020 MuK IT GmbH
# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class DmsDirectory(models.Model):
    _inherit = "dms.directory"

    has_versioning = fields.Boolean(
        default=False,
        help="Indicates if files have an active version control.",
    )

    @api.onchange("storage_id")
    def _onchange_storage_id(self):
        for record in self:
            if record.storage_id.save_type != "attachment" and record.is_root_directory:
                record.has_versioning = record.storage_id.has_versioning

    @api.onchange("parent_id")
    def _onchange_parent_id(self):
        for record in self:
            if record.parent_id:
                record.has_versioning = record.parent_id.has_versioning
