from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    dms_exemption_settings = fields.Boolean(
        related="company_id.documents_exemption_settings",
        readonly=False,
        string="Exemption",
    )
    dms_exemption_folder = fields.Many2one(
        "dms.directory",
        related="company_id.dms_exemption_folder",
        readonly=False,
        string="Exemption Default Workspace",
    )
    dms_exemption_category = fields.Many2one(
        "dms.category",
        related="dms_exemption_folder.category_id",
        readonly=False,
        string="Category",
    )
    dms_exemption_tags = fields.Many2many(
        "dms.tag",
        "exemption_tags_table",
        related="dms_exemption_folder.tag_ids",
        domain="""[
            '|', ['category_id', '=', False],
            ['category_id', 'child_of', dms_exemption_category]]
        """,
        readonly=False,
        string="Exemption Tags",
    )

    # @api.onchange("exemption_folder")
    # def on_exemption_folder_change(self):
    #     if self.exemption_folder not in self.exemption_tags.mapped("directory_ids"):
    #         self.exemption_tags = False
