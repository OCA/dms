# Copyright 2026 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class DmsDirectory(models.Model):
    _inherit = "dms.directory"

    dms_product_template_ids = fields.Many2many(
        comodel_name="product.template",
        relation="dms_directory_product_template_rel",
        column1="directory_id",
        column2="product_template_id",
    )
