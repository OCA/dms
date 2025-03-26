from odoo import fields, models


class ResPartnerExemption(models.Model):
    _name = "res.partner.exemption"
    _description = "Res Partner Exemption"
    _inherit = [
        "res.partner.exemption",
        "abstract.dms.mixin",
    ]

    document_link_id = fields.Many2one(
        "dms.file",
    )
