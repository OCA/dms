# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import re

from odoo import api, fields, models


class WizardDmsClassificationDetail(models.TransientModel):
    _inherit = "wizard.dms.classification.detail"

    template_id = fields.Many2one(related="parent_id.template_id")
    record_ref = fields.Reference(
        string="Record Referenced",
        compute="_compute_record_ref",
        selection=lambda self: self._get_ref_selection(),
    )

    @api.model
    def _get_ref_selection(self):
        models = self.env["ir.model"].sudo().search([("transient", "=", False)])
        return [(model.model, model.name) for model in models]

    @api.depends(
        "directory_id",
        "directory_id.root_directory_id",
        "directory_id.res_model",
        "directory_id.res_id",
    )
    def _compute_record_ref(self):
        """Set the linked record according to directory or root directory (to be
        correct if we are in a subdirectory)."""
        for record in self:
            directory = False
            if record.directory_id.res_model and record.directory_id.res_id:
                directory = record.directory_id
            elif (
                record.directory_id.root_directory_id.res_model
                and record.directory_id.root_directory_id.res_id
            ):
                directory = record.directory_id.root_directory_id
            record.record_ref = (
                f"{directory.res_model},{directory.res_id}" if directory else False
            )

    @api.depends("file_name", "template_id.model_id")
    def _compute_directory_id(self):
        """Overwrite to redefine the directory if the template has a linked model."""
        self_with_model = self.filtered(lambda x: x.template_id.model_id)
        directory_model = self.env["dms.directory"].sudo()
        for item in self_with_model:
            domain = [
                ("res_model", "=", item.template_id.model_id.model),
                ("res_id", ">", 0),
            ]
            directories = directory_model.search(domain)
            # We also add the subdirectorior because they are necessary and have not
            # set res_model and res_id
            directories += directories.mapped("child_directory_ids")
            if directories:
                matches = re.search(item.template_id.filename_pattern, item.file_name)
                if matches:
                    directory_pattern = item.template_id.directory_pattern
                    for detail in item.template_id.detail_ids:
                        matches_value = matches.groups()[detail.index]
                        # Change directory pattern if index in pattern
                        expected = f"{{{detail.index}}}"
                        if expected in directory_pattern:
                            directory_pattern = directory_pattern.replace(
                                expected, matches_value
                            )
                    # Search directories according to directory_pattern
                    item.directory_id = self.parent_id._get_directory_from_pattern(
                        directory_pattern, directories
                    )
        return super(
            WizardDmsClassificationDetail, (self - self_with_model)
        )._compute_directory_id()
