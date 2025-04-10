# Copyright 2025 Kencove (https://www.kencove.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import api, models


class DMSFile(models.Model):
    _inherit = "dms.file"

    @api.constrains("size")
    def _check_size(self):
        if self.env.context.get("bypass_check_size"):
            return
        super()._check_size()
