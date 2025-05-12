# Copyright 2025 Escodoo, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date

from odoo import api, fields, models


class DmsFile(models.Model):

    _inherit = "dms.file"

    expiry_date = fields.Date()
    days_to_expire = fields.Integer(
        compute="_compute_days_to_expire",
        readonly=True,
    )
    expiry_state = fields.Selection(
        selection=[
            ("valid", "Valid"),
            ("expiring_soon", "Expiring Soon"),
            ("expired", "Expired"),
        ],
        compute="_compute_expiry_state",
        store=True,
        readonly=True,
        default=False,
    )

    @api.depends("expiry_date")
    def _compute_days_to_expire(self):
        today = date.today()
        for file in self:
            if file.expiry_date:
                days = (file.expiry_date - today).days
                file.days_to_expire = days
            else:
                file.days_to_expire = 0
            file._compute_expiry_state()

    @api.depends("days_to_expire")
    def _compute_expiry_state(self):
        for file in self:
            if file.expiry_date:
                if file.days_to_expire < 0:
                    file.expiry_state = "expired"
                elif file.days_to_expire <= 30:
                    file.expiry_state = "expiring_soon"
                else:
                    file.expiry_state = "valid"
            else:
                file.expiry_state = False
