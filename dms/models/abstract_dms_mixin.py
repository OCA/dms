# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import odoo
from odoo import api, fields

from odoo.addons.web.models import models


class AbstractDmsMixin(odoo.models.AbstractModel):
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
    def search_panel_select_range(self, field_name):
        """We need to override function to prevent 200 records limit in search panel"""
        old_value = models.SEARCH_PANEL_LIMIT
        models.SEARCH_PANEL_LIMIT = False
        _self = self.with_context(directory_short_name=True)
        res = super(AbstractDmsMixin, _self).search_panel_select_range(field_name)
        all_ids = [value["id"] for value in res["values"]]
        # Prevent error if user not access to parent record
        for value in res["values"]:
            if value["parent_id"] and value["parent_id"][0] not in all_ids:
                value["parent_id"] = False
        models.SEARCH_PANEL_LIMIT = old_value
        return res
