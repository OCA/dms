# Copyright 2017-2019 MuK IT GmbH.
# Copyright 2020 Creu Blanca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import functools
import logging
import operator
from collections import defaultdict

from odoo import _, api, fields, models, tools
from odoo.exceptions import AccessError, ValidationError

from ..tools.file import check_name, unique_name

_logger = logging.getLogger(__name__)


class DmsDirectory(models.Model):

    _name = "dms.directory"
    _description = "Directory"

    _inherit = [
        "dms.security.mixin",
        "dms.mixins.thumbnail",
    ]

    _rec_name = "complete_name"
    _order = "complete_name"

    _parent_store = True
    _parent_name = "parent_id"

    name = fields.Char(string="Name", required=True, index=True)

    parent_path = fields.Char()
    is_root_directory = fields.Boolean(
        string="Is Root Directory",
        default=False,
        help="""Indicates if the directory is a root directory.
        A root directory has a settings object, while a directory with a set
        parent inherits the settings form its parent.""",
    )

    root_storage_id = fields.Many2one(
        comodel_name="dms.storage",
        string="Root Storage",
        ondelete="restrict",
        compute="_compute_directory_type",
        store=True,
        readonly=False,
        copy=True,
    )

    storage_id = fields.Many2one(
        compute="_compute_storage",
        comodel_name="dms.storage",
        string="Storage",
        ondelete="restrict",
        auto_join=True,
        readonly=True,
        store=True,
        copy=True,
    )

    parent_id = fields.Many2one(
        comodel_name="dms.directory",
        domain="[('permission_create', '=', True)]",
        string="Parent Directory",
        ondelete="restrict",
        auto_join=True,
        index=True,
        store=True,
        readonly=False,
        compute="_compute_directory_type",
        copy=True,
    )

    complete_name = fields.Char(
        "Complete Name", compute="_compute_complete_name", store=True
    )
    child_directory_ids = fields.One2many(
        comodel_name="dms.directory",
        inverse_name="parent_id",
        string="Subdirectories",
        auto_join=False,
        copy=False,
    )
    is_hidden = fields.Boolean(
        string="Storage is Hidden", related="storage_id.is_hidden", readonly=True
    )
    company_id = fields.Many2one(
        related="storage_id.company_id",
        comodel_name="res.company",
        string="Company",
        readonly=True,
        store=True,
        index=True,
    )

    color = fields.Integer(string="Color", default=0)

    category_id = fields.Many2one(
        comodel_name="dms.category",
        context="{'dms_category_show_path': True}",
        string="Category",
    )

    tag_ids = fields.Many2many(
        comodel_name="dms.tag",
        relation="dms_directory_tag_rel",
        domain="""[
            '|', ['category_id', '=', False],
            ['category_id', 'child_of', category_id]]
        """,
        column1="did",
        column2="tid",
        string="Tags",
        compute="_compute_tags",
        readonly=False,
        store=True,
    )

    user_star_ids = fields.Many2many(
        comodel_name="res.users",
        relation="dms_directory_star_rel",
        column1="did",
        column2="uid",
        string="Stars",
    )

    starred = fields.Boolean(
        compute="_compute_starred",
        inverse="_inverse_starred",
        search="_search_starred",
        string="Starred",
    )

    file_ids = fields.One2many(
        comodel_name="dms.file",
        inverse_name="directory_id",
        string="Files",
        auto_join=False,
        copy=False,
    )

    count_directories = fields.Integer(
        compute="_compute_count_directories", string="Count Subdirectories"
    )

    count_files = fields.Integer(compute="_compute_count_files", string="Count Files")

    count_elements = fields.Integer(
        compute="_compute_count_elements", string="Count Elements"
    )

    count_total_directories = fields.Integer(
        compute="_compute_count_total_directories", string="Total Subdirectories"
    )

    count_total_files = fields.Integer(
        compute="_compute_count_total_files", string="Total Files"
    )

    count_total_elements = fields.Integer(
        compute="_compute_count_total_elements", string="Total Elements"
    )

    size = fields.Integer(compute="_compute_size", string="Size")

    inherit_groups = fields.Boolean(string="Inherit Groups", default=True)

    # ----------------------------------------------------------
    # Functions
    # ----------------------------------------------------------

    def toggle_starred(self):
        updates = defaultdict(set)
        for record in self:
            vals = {"starred": not record.starred}
            updates[tools.frozendict(vals)].add(record.id)
        with self.env.norecompute():
            for vals, ids in updates.items():
                self.browse(ids).write(dict(vals))
        self.recompute()

    # ----------------------------------------------------------
    # Actions
    # ----------------------------------------------------------

    def action_save_onboarding_directory_step(self):
        self.env.user.company_id.set_onboarding_step_done(
            "documents_onboarding_directory_state"
        )

    # ----------------------------------------------------------
    # SearchPanel
    # ----------------------------------------------------------

    @api.model
    def _search_panel_directory(self, **kwargs):
        search_domain = (kwargs.get("search_domain", []),)
        if search_domain and len(search_domain):
            for domain in search_domain[0]:
                if domain[0] == "parent_id":
                    return domain[1], domain[2]
        return None, None

    # ----------------------------------------------------------
    # Search
    # ----------------------------------------------------------

    @api.model
    def _search_starred(self, operator, operand):
        if operator == "=" and operand:
            return [("user_star_ids", "in", [self.env.uid])]
        return [("user_star_ids", "not in", [self.env.uid])]

    # ----------------------------------------------------------
    # Read
    # ----------------------------------------------------------

    @api.depends("name", "parent_id.complete_name")
    def _compute_complete_name(self):
        for category in self:
            if category.parent_id:
                category.complete_name = "{} / {}".format(
                    category.parent_id.complete_name, category.name,
                )
            else:
                category.complete_name = category.name

    @api.depends("root_storage_id", "parent_id")
    def _compute_storage(self):
        for record in self:
            if record.is_root_directory:
                record.storage = record.root_storage_id
            else:
                record.storage = record.parent_id.storage_id

    @api.depends("user_star_ids")
    def _compute_starred(self):
        for record in self:
            record.starred = self.env.user in record.user_star_ids

    @api.depends("child_directory_ids")
    def _compute_count_directories(self):
        for record in self:
            record.count_directories = len(record.child_directory_ids)

    @api.depends("file_ids")
    def _compute_count_files(self):
        for record in self:
            record.count_files = len(record.file_ids)

    @api.depends("child_directory_ids", "file_ids")
    def _compute_count_elements(self):
        for record in self:
            elements = record.count_files
            elements += record.count_directories
            record.count_elements = elements

    def _compute_count_total_directories(self):
        for record in self:
            count = self.search_count([("id", "child_of", record.id)])
            count = count - 1 if count > 0 else 0
            record.count_total_directories = count

    def _compute_count_total_files(self):
        model = self.env["dms.file"]
        for record in self:
            record.count_total_files = model.search_count(
                [("directory_id", "child_of", record.id)]
            )

    def _compute_count_total_elements(self):
        for record in self:
            total_elements = record.count_total_files
            total_elements += record.count_total_directories
            record.count_total_elements = total_elements

    def _compute_size(self):
        sudo_model = self.env["dms.file"].sudo()
        for record in self:
            # Avoid NewId
            if not record.id:
                record.size = 0
                continue
            recs = sudo_model.search_read(
                domain=[("directory_id", "child_of", record.id)], fields=["size"],
            )
            record.size = sum(rec.get("size", 0) for rec in recs)

    @api.depends("inherit_groups", "parent_path")
    def _compute_groups(self):
        records = self.filtered(lambda record: record.parent_path)
        paths = [list(map(int, rec.parent_path.split("/")[:-1])) for rec in records]
        ids = paths and set(functools.reduce(operator.concat, paths)) or []
        read = self.browse(ids).read(["inherit_groups", "groups"])
        data = {entry.pop("id"): entry for entry in read}
        for record in records:
            complete_group_ids = set()
            for directory_id in reversed(
                list(map(int, record.parent_path.split("/")[:-1]))
            ):
                if directory_id in data:
                    complete_group_ids |= set(data[directory_id].get("groups", []))
                    if not data[directory_id].get("inherit_groups"):
                        break
            record.update({"complete_groups": [(6, 0, list(complete_group_ids))]})
        for record in self - records:
            if record.parent_id and record.inherit_groups:
                complete_groups = record.parent_id.complete_groups
                record.complete_groups = record.groups | complete_groups
            else:
                record.complete_groups = record.groups

    # ----------------------------------------------------------
    # View
    # ----------------------------------------------------------

    @api.depends("is_root_directory")
    def _compute_directory_type(self):
        for record in self:
            if record.is_root_directory:
                record.parent_id = None
            else:
                record.root_storage_id = None

    @api.depends("category_id")
    def _compute_tags(self):
        for record in self:
            tags = record.tag_ids.filtered(
                lambda rec: not rec.category_id or rec.category_id == record.category_id
            )
            record.tag_ids = tags

    # ----------------------------------------------------------
    # Constrains
    # ----------------------------------------------------------

    @api.constrains("parent_id")
    def _check_directory_recursion(self):
        if not self._check_recursion():
            raise ValidationError(_("Error! You cannot create recursive directories."))
        return True

    @api.constrains("is_root_directory", "root_storage_id", "parent_id")
    def _check_directory_storage(self):
        for record in self:
            if record.is_root_directory and not record.root_storage_id:
                raise ValidationError(_("A root directory has to have a root storage."))
            if not record.is_root_directory and not record.parent_id:
                raise ValidationError(_("A directory has to have a parent directory."))
            if record.parent_id and (
                record.is_root_directory or record.root_storage_id
            ):
                raise ValidationError(
                    _("A directory can't be a root and have a parent directory.")
                )

    @api.constrains("parent_id")
    def _check_directory_access(self):
        for record in self:
            if not record.parent_id.check_access("create", raise_exception=False):
                raise ValidationError(
                    _(
                        "The parent directory has to have the permission "
                        "to create directories."
                    )
                )

    @api.constrains("name")
    def _check_name(self):
        for record in self:
            if not check_name(record.name):
                raise ValidationError(_("The directory name is invalid."))
            if record.is_root_directory:
                childs = record.sudo().root_storage_id.root_directory_ids.name_get()
            else:
                childs = record.sudo().parent_id.child_directory_ids.name_get()
            if list(
                filter(
                    lambda child: child[1] == record.name and child[0] != record.id,
                    childs,
                )
            ):
                raise ValidationError(
                    _("A directory with the same name already exists.")
                )

    # ----------------------------------------------------------
    # Create, Update, Delete
    # ----------------------------------------------------------

    def _inverse_starred(self):
        starred_records = self.env["dms.directory"].sudo()
        not_starred_records = self.env["dms.directory"].sudo()
        for record in self:
            if not record.starred and self.env.user in record.user_star_ids:
                starred_records |= record
            elif record.starred and self.env.user not in record.user_star_ids:
                not_starred_records |= record
        not_starred_records.write({"user_star_ids": [(4, self.env.uid)]})
        starred_records.write({"user_star_ids": [(3, self.env.uid)]})

    @api.returns("self", lambda value: value.id)
    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or [])
        if "root_storage_id" in default:
            storage = self.env["dms.storage"].browse(default["root_storage_id"])
            names = storage.sudo().root_directory_ids.mapped("name")
        elif "parent_id" in default:
            parent_directory = self.browse(default["parent_id"])
            names = parent_directory.sudo().child_directory_ids.mapped("name")
        elif self.is_root_directory:
            names = self.sudo().root_storage_id.root_directory_ids.mapped("name")
        else:
            names = self.sudo().parent_id.child_directory_ids.mapped("name")
        default.update({"name": unique_name(self.name, names)})
        new = super().copy(default)
        for record in self.file_ids:
            record.copy({"directory_id": new.id})
        for record in self.child_directory_ids:
            record.copy({"parent_id": new.id})
        return new

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("root_storage_id", False):
                vals["storage_id"] = vals["root_storage_id"]
            if vals.get("parent_id", False):
                parent = self.browse([vals["parent_id"]])
                data = next(iter(parent.sudo().read(["storage_id"])), {})
                vals["storage_id"] = self._convert_to_write(data).get("storage_id")
        return super().create(vals_list)

    def write(self, vals):
        # Groups part
        if any(key in vals for key in ["groups", "inherit_groups"]):
            with self.env.norecompute():
                res = super(DmsDirectory, self).write(vals)
                domain = [("id", "child_of", self.ids)]
                records = self.sudo().search(domain)
                records.modified(["groups"])
            records.recompute()
        else:
            res = super().write(vals)

        if self and any(
            field for field in vals if field in ["root_storage_id", "parent_id"]
        ):
            records = self.sudo().search([("id", "child_of", self.ids)]) - self
            if "root_storage_id" in vals:
                records.write({"storage_id": vals["root_storage_id"]})
            elif "parent_id" in vals:
                parent = self.browse([vals["parent_id"]])
                data = next(iter(parent.sudo().read(["storage_id"])), {})
                records.write(
                    {"storage_id": self._convert_to_write(data).get("storage_id")}
                )
        return res

    def unlink(self):
        if self and self.check_access("unlink", raise_exception=True):
            domain = [
                "&",
                ("directory_id", "child_of", self.ids),
                "&",
                ("locked_by", "!=", self.env.uid),
                ("locked_by", "!=", False),
            ]
            if self.env["dms.file"].sudo().search(domain):
                raise AccessError(_("A file is locked, the folder cannot be deleted."))
            self.env["dms.file"].sudo().search(
                [("directory_id", "child_of", self.ids)]
            ).unlink()
            return super(
                DmsDirectory, self.sudo().search([("id", "child_of", self.ids)])
            ).unlink()
        return super().unlink()
