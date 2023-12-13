# Copyright 2022 CreuBlanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class DmsStorage(models.Model):
    _inherit = "dms.storage"

    save_type = fields.Selection(
        selection_add=[("storage", "Storage")], ondelete={"storage": "cascade"}
    )
    storage_backend_id = fields.Many2one("fs.storage")
