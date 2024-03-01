# Copyright 2017-2020 MuK IT GmbH
# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class DmsStorage(models.Model):
    _inherit = "dms.storage"

    has_versioning = fields.Boolean(
        default=False,
        help="Indicates if files have an active version control.",
    )

    @api.constrains("has_versioning")
    def _check_can_be_versioned(self):
        for storage in self:
            if storage.has_versioning and storage.save_type == "attachment":
                raise ValidationError(_("Attachment storages cannot be versioned."))
