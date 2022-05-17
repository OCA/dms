# Copyright 2022 CreuBlanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class DmsAction(models.Model):

    _name = "dms.action"
    _description = "DMS Action"

    name = fields.Char(required=True)
    kind = fields.Selection([("server_action", "Server Action")], required=True)
    icon = fields.Char()
    active = fields.Boolean(default=True)
    action_id = fields.Many2one(
        "ir.actions.server", domain=[("model_name", "=", "dms.file")]
    )
    dms_directory_ids = fields.Many2many("dms.directory")

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
