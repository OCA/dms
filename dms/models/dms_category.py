# Copyright 2020 Creu Blanca
# Copyright 2017-2019 MuK IT GmbH
# Copyright 2024 Subteno - Timothée Vannier (https://www.subteno.com).
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class DMSCategory(models.Model):
    _name = "dms.category"
    _description = "Document Category"

    _parent_store = True
    _parent_name = "parent_id"

    _order = "complete_name asc"
    _rec_name = "complete_name"

    name = fields.Char(required=True, translate=True)
    active = fields.Boolean(
        default=True,
        help="The active field allows you to hide the category without removing it.",
    )
    code = fields.Char()
    complete_name = fields.Char(
        compute="_compute_complete_name", store=True, recursive=True
    )
    parent_id = fields.Many2one(
        string="Parent Category",
        comodel_name="dms.category",
        ondelete="cascade",
        index="btree",
    )
    child_category_ids = fields.One2many(
        string="Child Categories",
        comodel_name="dms.category",
        inverse_name="parent_id",
    )
    parent_path = fields.Char(index="btree")
    tag_ids = fields.One2many(
        string="Tags", comodel_name="dms.tag", inverse_name="category_id"
    )
    directory_ids = fields.One2many(
        string="Directories",
        comodel_name="dms.directory",
        inverse_name="category_id",
        readonly=True,
    )
    file_ids = fields.One2many(
        string="Files",
        comodel_name="dms.file",
        inverse_name="category_id",
        readonly=True,
    )
    count_categories = fields.Integer(
        string="Count Subcategories", compute="_compute_count_categories"
    )
    count_tags = fields.Integer(compute="_compute_count_tags")
    count_directories = fields.Integer(compute="_compute_count_directories")
    count_files = fields.Integer(compute="_compute_count_files")

    _sql_constraints = [
        ("code_uniq", "unique (code)", "Category code already exists!"),
        ("name_uniq", "unique (name)", "Category name already exists!"),
    ]

    @api.depends("code", "name", "parent_id.complete_name")
    def _compute_complete_name(self):
        for category in self:
            name = category.name
            if code := category.code:
                name = f"[{code}] {name}"
            if category.parent_id:
                category.complete_name = f"{category.parent_id.complete_name} / {name}"
            else:
                category.complete_name = name

    @api.depends("child_category_ids")
    def _compute_count_categories(self):
        for record in self:
            record.count_categories = len(record.child_category_ids)

    @api.depends("tag_ids")
    def _compute_count_tags(self):
        for record in self:
            record.count_tags = len(record.tag_ids)

    @api.depends("directory_ids")
    def _compute_count_directories(self):
        for record in self:
            record.count_directories = len(record.directory_ids)

    @api.depends("file_ids")
    def _compute_count_files(self):
        for record in self:
            record.count_files = len(record.file_ids)

    @api.constrains("parent_id")
    def _check_category_recursion(self):
        if self._has_cycle():
            raise ValidationError(_("Error! You cannot create recursive categories."))
        return True

    def copy_data(self, default=None):
        vals_list = super().copy_data(default=default)
        if not (default or {}).get("code"):
            for category, vals in zip(self, vals_list, strict=False):
                if code := category.code:
                    vals["code"] = category.env._(
                        "%(categ_code)s (Copy)", categ_code=code
                    )
                vals["name"] = category.env._(
                    "%(categ_name)s (Copy)", categ_name=category.name
                )
        return vals_list
