# Copyright 2022 CreuBlanca
# Copyright 2026 Tecnativa - Adasat Torres
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command, _, api, fields, models


class DmsAction(models.Model):
    _name = "dms.action"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "DMS Action"

    name = fields.Char(required=True)
    kind = fields.Selection([("server_action", "Server Action")], required=True)
    icon = fields.Char()
    active = fields.Boolean(default=True)
    action_id = fields.Many2one(
        "ir.actions.server",
        domain=[("model_name", "=", "dms.file")],
        help="Server action to execute when this action is triggered. "
        "Only server actions that are configured to run on the model "
        "'DMS File' are available for selection.",
    )
    dms_directory_ids = fields.Many2many(
        "dms.directory",
        string="Directories",
        help="Directories whose files can use this action. The action is also "
        "available recursively in all their subdirectories, without having "
        "to select each subdirectory individually. Allowed group restrictions "
        "still apply.",
    )
    group_ids = fields.Many2many(
        "res.groups",
        string="Allowed Groups",
        help="Leave empty to allow all DMS users. Otherwise, users must belong "
        "to at least one of these groups to see and execute the action.",
    )

    tags_action_ids = fields.One2many(
        "dms.action.tag.action", "dms_action_id", string="Tags Actions"
    )

    @api.model
    def _get_available_domain(self):
        # An empty group list grants access; otherwise, one matching group is enough.
        return [
            "|",
            ("group_ids", "=", False),
            ("group_ids", "in", self.env.user.groups_id.ids),
        ]

    def _execute_action(self, file):
        # Dispatch to the handler associated with the configured action kind.
        res = getattr(self, "_execute_%s" % self.kind)(file)
        self.tags_action_ids.execute_actions(file)
        return res

    def _execute_server_action(self, file):
        file.ensure_one()
        self.ensure_one()
        # Server actions use the active record from the context as their target.
        return self.action_id.with_context(
            active_model=file._name, active_id=file.id
        ).run()

    def _get_json_data(self):
        return {
            "name": self.name,
            "icon": self.icon,
        }


class DmsActionTagAction(models.Model):
    _name = "dms.action.tag.action"
    _description = "DMS Action Tags Action"
    _sql_constraints = [
        (
            "dms_action_id_category_id_tag_id_uniq",
            "unique(action, category_id, tag_id)",
            "The combination of action, category and tag must be unique.",
        )
    ]
    _order = "sequence, id"

    dms_action_id = fields.Many2one("dms.action", required=True)
    sequence = fields.Integer(default=10)
    action = fields.Selection(
        [("add", "Add"), ("remove", "Remove"), ("replace", "Replace")], required=True
    )
    category_id = fields.Many2one("dms.category", required=True)
    tag_id = fields.Many2one("dms.tag", required=True)

    @api.model
    def execute_actions(self, file):
        for tag_action in self:
            getattr(tag_action, "_execute_action_%s" % tag_action.action)(file)
        return True

    def _execute_action_add(self, file):
        # Add the tag to the file if it's not already present.
        if self.tag_id not in file.tag_ids:
            file.tag_ids = [Command.link(self.tag_id.id)]
        return True

    def _execute_action_remove(self, file):
        # Remove the tag from the file if it's present.
        if self.tag_id in file.tag_ids:
            file.tag_ids = [Command.unlink(self.tag_id.id)]
        return True

    def _execute_action_replace(self, file):
        # Remove all tags in the same category and add the new tag.
        existing_tags = file.tag_ids.filtered(
            lambda t: t.category_id == self.category_id
        )
        command_list = [Command.unlink(tag.id) for tag in existing_tags]
        command_list.append(Command.link(self.tag_id.id))
        file.tag_ids = command_list
        return True

    @api.constrains("tag_id", "category_id")
    def _check_tag_category(self):
        for record in self:
            if record.tag_id.category_id != record.category_id:
                raise models.ValidationError(
                    _("The selected tag does not belong to the specified category.")
                )
