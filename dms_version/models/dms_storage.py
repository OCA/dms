# Copyright 2017-2020 MuK IT GmbH
# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class DmsStorage(models.Model):
    _inherit = "dms.storage"

    has_versioning = fields.Boolean(
        default=False,
        help="Indicates if files have an active version control.",
    )
