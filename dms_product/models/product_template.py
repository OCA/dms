# Copyright 2026 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    dms_directory_ids = fields.Many2many(
        comodel_name="dms.directory",
        relation="dms_directory_product_template_rel",
        column1="product_template_id",
        column2="directory_id",
        string="Directories",
    )
    dms_file_ids = fields.Many2many(
        comodel_name="dms.file",
        compute="_compute_dms_file_ids",
        string="Files",
    )

    @api.depends("dms_directory_ids.file_ids")
    def _compute_dms_file_ids(self):
        for product in self:
            product.dms_file_ids = product.dms_directory_ids.file_ids
