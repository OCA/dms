# Copyright 2024 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class DmsAccessGroups(models.Model):
    _inherit = "dms.access.group"

    dms_field_ref = fields.Reference(
        selection="_selection_reference_value",
        string="DMS field reference",
    )

    @api.model
    def _selection_reference_value(self):
        models = (
            self.env["ir.model"]
            .sudo()
            .search([("transient", "=", False)], order="name asc")
        )
        return [(model.model, model.name) for model in models]

    def _get_item_from_dms_field_ref(self, record):
        return self.env["dms.access.group"].search(
            [("dms_field_ref", "=", "%s,%s" % (record._name, record.id))]
        )

    @api.constrains("dms_field_ref")
    def _check_dms_field_ref(self):
        for item in self.filtered("dms_field_ref"):
            dms_field_ref = "%s,%s" % (item.dms_field_ref._name, item.dms_field_ref.id)
            if self.search(
                [("dms_field_ref", "=", dms_field_ref), ("id", "!=", item.id)]
            ):
                raise UserError(
                    _("There is already an access group created for this record.")
                )
