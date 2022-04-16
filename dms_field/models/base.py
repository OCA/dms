# Copyright 2020 Creu Blanca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class Base(models.AbstractModel):
    _inherit = "base"

    dms_directory_ids = fields.One2many(
        "dms.directory",
        "res_id",
        string="DMS Directories",
        domain=lambda self: [
            ("res_model", "=", self._name),
            ("storage_id.save_type", "!=", "attachment"),
        ],
        auto_join=True,
    )
