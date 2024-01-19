# Copyright 2020 Creu Blanca
# Copyright 2024 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class Base(models.AbstractModel):
    _inherit = "base"

    dms_directory_ids = fields.One2many(
        "dms.directory",
        "res_id",
        string="DMS Directories",
        domain=lambda self: [
            ("res_model", "=", self._name),
            ("storage_id.save_type", "!=", "attachment"),
        ],
        auto_join=True,
    )

    @api.model
    def models_to_track_dms_field_template(self):
        """Models to be tracked for dms field templates
        :args:
        :returns: list of models
        """
        return self.env["dms.field.template"].sudo().search([]).mapped("model_id.model")

    @api.model_create_multi
    def create(self, vals_list):
        """Create a dms directory when creating the record if exist a template."""
        result = super().create(vals_list)
        if (
            not self.env.context.get("skip_track_dms_field_template")
            and self._name in self.models_to_track_dms_field_template()
        ):
            template = self.env["dms.field.template"].with_context(res_model=self._name)
            for item in result:
                template.with_context(res_id=item.id).create_dms_directory()
        return result
