# Copyright 2025 APSL-Nagarro - Miquel Alzanillas, Antoni Marroig
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class DmsFile(models.Model):
    _inherit = "dms.file"

    _sql_constraints = [
        # Ensure compatibility with other modules that always expect a value in name
        ("name_required", "CHECK(name IS NOT NULL)", "File name is required"),
        (
            "sequence_code_unique",
            "UNIQUE(sequence_code)",
            "Sequence code must be unique",
        ),
    ]

    sequence_code = fields.Char(
        copy=False,
        readonly=True,
    )

    name = fields.Char(
        # We actually require it with the SQL constraint, but it is disabled
        # here to let users create/write dms records without name, and let this module
        # add a default name if needed
        required=False,
    )

    @api.depends("sequence_code", "name")
    def _compute_display_name(self):
        res = super()._compute_display_name()
        sequence_pattern = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(
                "dms_file_sequence.display_name_pattern",
                default="%(sequence_code)s - %(name)s",
            )
        )
        for dms_file in self.filtered(
            lambda file: file.sequence_code and file.sequence_code != file.name
        ):
            dms_file.display_name = sequence_pattern % {
                "name": dms_file.name,
                "sequence_code": dms_file.sequence_code,
            }
        return res

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        """Allow searching by sequence code by default."""
        # Do not add any domain when user just clicked on search widget
        if not (name == "" and operator == "ilike"):
            # The dangling | is needed to combine with the domain added by super()
            args = (args or []) + ["|", ("sequence_code", operator, name)]
        return super().name_search(name, args, operator, limit)

    @api.model_create_multi
    def create(self, vals_list):
        """Apply sequence code and a default name if not set."""
        for vals in vals_list:
            if "sequence_code" not in vals:
                vals["sequence_code"] = self.env["ir.sequence"].next_by_code(
                    "dms.file.sequence"
                )
            if not vals.get("name"):
                vals["name"] = vals["sequence_code"]
        res = super().create(vals_list)
        return res
