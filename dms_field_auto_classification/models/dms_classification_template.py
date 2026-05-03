# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class DmsClassificationTemplate(models.Model):
    _inherit = "dms.classification.template"

    model_id = fields.Many2one(
        comodel_name="ir.model", string="Model", domain=[("transient", "=", False)]
    )
    model = fields.Char(
        compute="_compute_model", string="Model name", compute_sudo=True
    )
    detail_ids = fields.One2many(
        string="Details",
        comodel_name="dms.classification.template.detail",
        inverse_name="parent_id",
    )

    @api.depends("model_id")
    def _compute_model(self):
        for item in self:
            item.model = item.model_id.model


class DmsClassificationTemplateDetail(models.Model):
    _name = "dms.classification.template.detail"
    _description = "Dms Classification Template Detail"
    _order = "sequence, field_id"

    parent_id = fields.Many2one(
        comodel_name="dms.classification.template",
        string="Parent",
    )
    model_id = fields.Many2one(
        related="parent_id.model_id",
    )
    field_id = fields.Many2one(
        comodel_name="ir.model.fields",
        domain="[('model_id', '=', model_id)]",
        string="Field",
    )
    index = fields.Integer(required=True, default=0)
    sequence = fields.Integer(required=True, default=10)
