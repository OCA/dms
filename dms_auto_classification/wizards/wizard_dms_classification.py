# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
import base64
import re
import zipfile
from io import BytesIO

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class WizardDmsClassification(models.TransientModel):
    _name = "wizard.dms.classification"
    _description = "Wizard Dms Classification"

    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("analyze", "Analyze"),
        ],
        default="draft",
    )
    template_id = fields.Many2one(
        comodel_name="dms.classification.template",
        string="Template",
        required=True,
    )
    data_file = fields.Binary(
        string="File",
        required=True,
    )
    data_filename = fields.Char()
    detail_ids = fields.One2many(
        comodel_name="wizard.dms.classification.detail",
        inverse_name="parent_id",
        string="Details",
    )

    def _is_zipfile(self):
        try:
            zipfile.ZipFile(BytesIO(base64.b64decode(self.data_file)))
            return True
        except (zipfile.BadZipFile, ValueError):
            return False

    @api.onchange("data_file")
    def _onchange_data_file(self):
        for item in self.filtered("data_file"):
            if not item._is_zipfile():
                raise UserError(_("Only .zip files are allowed"))

    def _return_item(self):
        return {
            "context": self.env.context,
            "view_type": "form",
            "view_mode": "form",
            "res_model": self._name,
            "res_id": self.id,
            "view_id": False,
            "type": "ir.actions.act_window",
            "target": "new",
        }

    def _get_directory_from_pattern(self, pattern, directories):
        directory = False
        for d in directories:
            if re.search(pattern, d.complete_name):
                directory = d
                break
        return directory

    def action_analyze(self):
        """Process the zip file and generate details."""
        details = self._prepare_details_vals()
        self.state = "analyze"
        self.detail_ids = [(0, 0, vals) for vals in details]
        return self._return_item()

    def _prepare_details_vals(self):
        """Method that gets the files from .zip and if it apply the filename pattern
        it will set it as detail with the corresponding values."""
        details = []
        zip_file = zipfile.ZipFile(BytesIO(base64.b64decode(self.data_file)))
        filename_pattern = self.template_id.filename_pattern
        for filename in zip_file.namelist():
            if re.search(filename_pattern, filename):
                file_content = zip_file.read(filename)
                data_file = base64.b64encode(file_content)
                details.append(self._prepare_detail_vals(filename, data_file))
        return details

    def _prepare_detail_vals(self, file_name, data_file):
        """Method to set the values of each detail. May be extended by other modules."""
        return {
            "file_name": file_name,
            "data_file": data_file,
        }

    def _action_classify(self):
        """Create the files (dms.file) in the corresponding directory.
        Details that do not have a directory or already have a linked
        file are skipped."""
        for detail in self.detail_ids.filtered(
            lambda x: x.state == "to_classify" and x.directory_id
        ):
            detail._create_dms_file()

    def action_classify(self):
        self._action_classify()
        action = self.env["ir.actions.act_window"]._for_xml_id("dms.action_dms_file")
        action["view_mode"] = "tree"
        action["views"] = [(False, "tree")]
        action["domain"] = [("id", "in", self.mapped("detail_ids.file_id").ids)]
        return action


class WizardDmsClassificationDetail(models.TransientModel):
    _name = "wizard.dms.classification.detail"
    _description = "Wizard Dms Classification Detail"

    parent_id = fields.Many2one(
        comodel_name="wizard.dms.classification",
        string="Parent",
    )
    file_name = fields.Char(
        string="File name",
        required=True,
        readonly="True",
    )
    data_file = fields.Binary(
        string="File",
        required=True,
    )
    directory_id = fields.Many2one(
        comodel_name="dms.directory",
        string="Directory",
        compute="_compute_directory_id",
        store=True,
        readonly=False,
    )
    file_id = fields.Many2one(
        comodel_name="dms.file",
        string="File",
        compute="_compute_file_id",
        store=True,
        readonly=True,
    )
    state = fields.Selection(
        selection=[
            ("to_classify", "To classify"),
            ("classified", "Classified"),
        ],
        compute="_compute_state",
        store=True,
        readonly=True,
    )

    @api.depends("file_name")
    def _compute_directory_id(self):
        directories = self.env["dms.directory"].sudo().search([])
        for item in self:
            item.directory_id = self.parent_id._get_directory_from_pattern(
                self.parent_id.template_id.directory_pattern, directories
            )

    @api.depends("file_name", "directory_id", "parent_id.state")
    def _compute_file_id(self):
        for item in self.filtered(lambda x: x.file_name and x.directory_id):
            files = item.directory_id.file_ids.filtered(
                lambda x: x.name == item.file_name
            )
            item.file_id = fields.first(files)

    @api.depends("file_id")
    def _compute_state(self):
        items_with_file = self.filtered("file_id")
        items_with_file.state = "classified"
        (self - items_with_file).state = "to_classify"

    def _create_dms_file(self):
        self.ensure_one()
        if not self.directory_id or self.file_id:
            return
        self.file_id = self.env["dms.file"].create(
            {
                "name": self.file_name,
                "directory_id": self.directory_id.id,
                "content": self.data_file,
            }
        )
