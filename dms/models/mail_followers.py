# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import api, fields, models


class MailFollowers(models.Model):
    _inherit = "mail.followers"

    dms_directory_id = fields.Many2one(comodel_name="dms.directory", string="File id")

    def _dms_operations(self):
        for item in self:
            item.dms_directory_id = (
                self.env["dms.directory"]
                .sudo()
                .search(
                    [
                        ("res_model", "=", item.res_model),
                        ("res_id", "=", item.res_id),
                        ("record_mail_followers_sync", "=", True),
                    ],
                    limit=1,
                )
            )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._dms_operations()
        return records
