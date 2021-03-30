# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AbstractDmsMixin(models.AbstractModel):
    _name = "abstract.dms.mixin"
    _description = "Abstract Dms Mixin"

    name = fields.Char(string="Name", required=True, index=True)
    res_model = fields.Char(string="Linked attachments model")
    res_id = fields.Integer(string="Linked attachments record ID")
    record_ref = fields.Reference(
        string="Record Referenced",
        compute="_compute_record_ref",
        selection=lambda self: self._get_ref_selection(),
    )
    # Only defined to prevent error in other fields that related it
    storage_id = fields.Many2one(
        comodel_name="dms.storage", string="Storage", store=True,
    )
    is_hidden = fields.Boolean(
        string="Storage is Hidden",
        related="storage_id.is_hidden",
        related_sudo=True,
        auto_join=True,
        readonly=True,
        store=True,
    )
    company_id = fields.Many2one(
        related="storage_id.company_id",
        related_sudo=True,
        auto_join=True,
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
    def _get_ref_selection(self):
        models = self.env["ir.model"].search([])
        return [(model.model, model.name) for model in models]

    @api.depends("res_model", "res_id")
    def _compute_record_ref(self):
        for record in self:
            record.record_ref = False
            if record.res_model and record.res_id:
                record.record_ref = "{},{}".format(record.res_model, record.res_id)
