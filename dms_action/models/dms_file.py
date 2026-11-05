# Copyright 2022 CreuBlanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class DmsFile(models.Model):
    _inherit = "dms.file"

    action_button = fields.Serialized(compute="_compute_action_button")
    with_actions = fields.Boolean(compute="_compute_action_button")

    @api.depends("directory_id", "directory_id.parent_path")
    # Available actions depend on the current user's group membership.
    @api.depends_context("uid")
    def _compute_action_button(self):
        # Index the button data by directory to reuse it across files in the batch.
        actions_by_directory = {}
        for directory in self.directory_id:
            # parent_of includes the directory itself and all its ancestors.
            actions = self.env["dms.action"].search(
                [("dms_directory_ids", "parent_of", directory.ids)]
                + self.env["dms.action"]._get_available_domain()
            )
            actions_by_directory[directory.id] = {
                action.id: action._get_json_data() for action in actions
            }
        for record in self:
            record.action_button = actions_by_directory.get(record.directory_id.id, {})
            record.with_actions = bool(record.action_button)

    def execute_action(self, kwargs=False):
        if not kwargs:
            return
        self.ensure_one()
        # Recheck directory and group restrictions when executing: hiding the
        # button alone does not prevent a direct RPC call.
        action = self.env["dms.action"].search(
            [
                ("id", "=", kwargs["action_id"]),
                ("dms_directory_ids", "parent_of", self.directory_id.ids),
            ]
            + self.env["dms.action"]._get_available_domain(),
            limit=1,
        )
        if not action:
            raise ValidationError(_("Action is not allowed"))
        return action._execute_action(self)
