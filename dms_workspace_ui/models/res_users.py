from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    dms_ui_custom_theme = fields.Selection(
        selection=[
            ("purple", "Purple"),
            ("teal", "Teal"),
            ("charcoal", "Charcoal"),
            ("blue", "Blue"),
            ("green", "Green"),
            ("red", "Red"),
            ("cyan", "Cyan"),
            ("amber", "Amber"),
        ],
        string="Documents Color Scheme",
        default="purple",
    )

    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + [
            "dms_ui_custom_theme",
        ]

    @property
    def SELF_WRITEABLE_FIELDS(self):
        return super().SELF_WRITEABLE_FIELDS + [
            "dms_ui_custom_theme",
        ]

    @api.model
    def dms_ui_action_documents(self):
        return self.env["ir.actions.act_window"]._for_xml_id(
            "dms_workspace_ui.action_dms_ui_file_workspace"
        )
