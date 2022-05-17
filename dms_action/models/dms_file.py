# Copyright 2022 CreuBlanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class DmsFile(models.Model):
    _inherit = "dms.file"

    action_button = fields.Serialized(compute="_compute_action_button")
    with_actions = fields.Boolean(compute="_compute_action_button")

    @api.depends("directory_id")
    def _compute_action_button(self):
        for record in self:
            record.action_button = {
                action.id: action._get_json_data()
                for action in record.directory_id.dms_action_ids
            }
            record.with_actions = len(record.action_button)

    def execute_action(self, kwargs=False):
        if not kwargs:
            return
        action = self.env["dms.action"].browse(kwargs["action_id"])
        if self.directory_id not in action.dms_directory_ids:
            raise ValidationError(_("Action is not allowed"))
        return action._execute_action(self)
