# Copyright 2022 CreuBlanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class DmsAction(models.Model):
    _name = "dms.action"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "DMS Action"

    name = fields.Char(required=True)
    kind = fields.Selection([("server_action", "Server Action")], required=True)
    icon = fields.Char()
    active = fields.Boolean(default=True)
    action_id = fields.Many2one(
        "ir.actions.server", domain=[("model_name", "=", "dms.file")]
    )
    dms_directory_ids = fields.Many2many("dms.directory", string="Directories")
    group_ids = fields.Many2many(
        "res.groups",
        string="Allowed Groups",
        help="Leave empty to allow all DMS users. Otherwise, users must belong "
        "to at least one of these groups to see and execute the action.",
    )

    @api.model
    def _get_available_domain(self):
        return [
            "|",
            ("group_ids", "=", False),
            ("group_ids", "in", self.env.user.groups_id.ids),
        ]

    def _execute_action(self, file):
        return getattr(self, "_execute_%s" % self.kind)(file)

    def _execute_server_action(self, file):
        file.ensure_one()
        self.ensure_one()
        return self.action_id.with_context(
            active_model=file._name, active_id=file.id
        ).run()

    def _get_json_data(self):
        return {
            "name": self.name,
            "icon": self.icon,
        }
