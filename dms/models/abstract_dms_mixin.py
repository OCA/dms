# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AbstractDmsMixin(models.AbstractModel):
    _name = "abstract.dms.mixin"
    _description = "Abstract Dms Mixin"

    name = fields.Char(required=True, index=True)
    # Only defined to prevent error in other fields that related it
    storage_id = fields.Many2one(
        comodel_name="dms.storage", string="Storage", store=True, copy=True
    )
    is_hidden = fields.Boolean(
        string="Storage is Hidden",
        related="storage_id.is_hidden",
        readonly=True,
        store=True,
    )
    company_id = fields.Many2one(
        related="storage_id.company_id",
        comodel_name="res.company",
        string="Company",
        readonly=True,
        store=True,
        index=True,
    )
    storage_id_save_type = fields.Selection(related="storage_id.save_type", store=False)
    color = fields.Integer(default=0)
    category_id = fields.Many2one(
        comodel_name="dms.category",
        context="{'dms_category_show_path': True}",
        string="Category",
    )
