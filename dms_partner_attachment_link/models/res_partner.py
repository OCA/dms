# Copyright (C) 2024 Cetmix OÜ
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class Partner(models.Model):
    _inherit = "res.partner"

    dms_file_count = fields.Integer(compute="_compute_dms_file_count")

    def _compute_dms_file_count(self):
        """
        Compute the number of DMS files
        related to these partners
        """
        for partner in self:
            partner.dms_file_count = self.env["dms.file"].search_count(
                [
                    ("res_id", "=", partner.id),
                    ("res_model", "=", "res.partner"),
                    ("storage_id.save_type", "=", "attachment"),
                ]
            )

    def action_open_dms_attachments(self):
        """
        Open action windows for DMS attachments
        related to this partner

        :return: Action Window
        :rtype: dict
        """
        self.ensure_one()
        action = self.env.ref("dms.action_dms_file").read()[0]
        action.update(
            {
                "domain": [
                    ("res_id", "=", self.id),
                    ("res_model", "=", "res.partner"),
                    ("storage_id.save_type", "=", "attachment"),
                ],
                "context": {
                    "default_res_id": self.id,
                    "default_res_model": "res.partner",
                },
            }
        )
        return action
