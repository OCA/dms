# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AbstractDmsMixin(models.AbstractModel):
    _name = "abstract.dms.mixin"
    _description = "Abstract Dms Mixin"

    name = fields.Char(string="Name", required=True, index=True)
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
    color = fields.Integer(string="Color", default=0)
    category_id = fields.Many2one(
        comodel_name="dms.category",
        context="{'dms_category_show_path': True}",
        string="Category",
    )

    @api.model
    def search_panel_select_range(self, field_name, **kwargs):
        """Remove the limit of records (default is 200 since js)."""
        kwargs.update(limit=False)
        _self = self.with_context(directory_short_name=True)
        return super(AbstractDmsMixin, _self).search_panel_select_range(
            field_name, **kwargs
        )
