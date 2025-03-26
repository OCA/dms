from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    def _domain_company(self):
        company = self.env.company
        return ["|", ("company_id", "=", False), ("company_id", "=", company)]

    documents_exemption_settings = fields.Boolean()
    dms_exemption_folder = fields.Many2one(
        "dms.directory",
        string="Exemption Workspace",
        domain=_domain_company,
        default=lambda self: self.env.ref(
            "dms_account_avatax_exemption.dms_exemption_folder",
            raise_if_not_found=False,
        ),
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
