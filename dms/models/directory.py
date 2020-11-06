# Copyright 2017-2019 MuK IT GmbH.
# Copyright 2020 Creu Blanca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64
import functools
import logging
import operator
from collections import defaultdict

from odoo import _, api, fields, models, tools
from odoo.exceptions import AccessError, ValidationError

from odoo.addons.http_routing.models.ir_http import slugify

from ..tools.file import check_name, unique_name

_logger = logging.getLogger(__name__)


class DmsDirectory(models.Model):

    _name = "dms.directory"
    _description = "Directory"

    _inherit = [
        "portal.mixin",
        "dms.security.mixin",
        "dms.mixins.thumbnail",
        "mail.thread",
        "mail.activity.mixin",
        "mail.alias.mixin",
    ]

    _rec_name = "complete_name"
    _order = "complete_name"

    _parent_store = True
    _parent_name = "parent_id"

    name = fields.Char(string="Name", required=True, index=True)

    parent_path = fields.Char(index=True)
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
        store=True,
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
        compute="_compute_count_directories", string="Count Subdirectories Title"
    )

    count_files = fields.Integer(
        compute="_compute_count_files", string="Count Files Title"
    )

    count_directories_title = fields.Char(
        compute="_compute_count_directories", string="Count Subdirectories"
    )

    count_files_title = fields.Char(
        compute="_compute_count_files", string="Count Files"
    )

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

    inherit_group_ids = fields.Boolean(string="Inherit Groups", default=True)

    alias_process = fields.Selection(
        selection=[("files", "Single Files"), ("directory", "Subdirectory")],
        required=True,
        default="directory",
        string="Unpack Emails as",
        help="""\
                Define how incoming emails are processed:\n
                - Single Files: The email gets attached to the directory and
                all attachments are created as files.\n
                - Subdirectory: A new subdirectory is created for each email
                and the mail is attached to this subdirectory. The attachments
                are created as files of the subdirectory.
                """,
    )

    def _get_share_url(self, redirect=False, signup_partner=False, pid=None):
        self.ensure_one()
        return "/my/dms/directory/{}?access_token={}&db={}".format(
            self.id, self._portal_ensure_token(), self.env.cr.dbname,
        )

    def check_access_token(self, access_token=False):
        res = False
        if access_token:
            items = self.env["dms.directory"].search(
                [("access_token", "=", access_token)]
            )
            if items:
                item = items[0]
                if item.id == self.id:
                    return True
                else:
                    directory_item = self
                    while directory_item.parent_id:
                        if directory_item.id == item.id:
                            return True
                        directory_item = directory_item.parent_id
                    # Fix last level
                    if directory_item.id == item.id:
                        return True
        return res

    @api.model
    def _get_parent_categories(self, access_token):
        self.ensure_one()
        directories = [self]
        current_directory = self
        if access_token:
            # Only show parent categories to access_token
            stop = False
            while current_directory.parent_id and not stop:
                if current_directory.access_token == access_token:
                    stop = False
                else:
                    directories.append(current_directory.parent_id)
                current_directory = current_directory.parent_id
        else:
            while (
                current_directory.parent_id
                and current_directory.parent_id.check_access("read", False)
            ):
                directories.append(current_directory.parent_id)
                current_directory = current_directory.parent_id
        return directories[::-1]

    def _get_own_root_directories(self, user_id):
        ids = []
        items = (
            self.env["dms.directory"]
            .with_user(user_id)
            .search([("is_hidden", "=", False)])
        )
        for item in items:
            current_directory = item
            while (
                current_directory.parent_id
                and current_directory.parent_id.check_access("read", False)
            ):
                current_directory = current_directory.parent_id

            if current_directory.id not in ids:
                ids.append(current_directory.id)

        return ids

    def check_access(self, operation, raise_exception=False):
        res = super(DmsDirectory, self).check_access(operation, raise_exception)
        if self.env.user.has_group("base.group_portal"):
            if self.id in self._get_ids_without_access_groups(operation):
                res = False
        # Fix show breadcrumb with share button (public)
        if self.env.user.has_group("base.group_public"):
            res = True
        return res

    allowed_model_ids = fields.Many2many(
        compute="_compute_allowed_model_ids", comodel_name="ir.model", store=False
    )
    model_id = fields.Many2one(
        comodel_name="ir.model",
        domain="[('id', 'in', allowed_model_ids)]",
        compute="_compute_model_id",
        inverse="_inverse_model_id",
        string="Model",
        store=True,
    )
    res_model = fields.Char(string="Linked attachments model")
    res_id = fields.Integer(string="Linked attachments record ID")
    record_ref = fields.Reference(
        string="Record Referenced", compute="_compute_record_ref", selection=[]
    )
    storage_id_save_type = fields.Selection(related="storage_id.save_type", store=False)

    @api.depends("root_storage_id", "storage_id")
    def _compute_allowed_model_ids(self):
        for record in self:
            record.allowed_model_ids = False
            if record.root_storage_id and record.root_storage_id.model_ids:
                record.allowed_model_ids = record.root_storage_id.model_ids.ids
            elif record.storage_id and record.storage_id.model_ids:
                record.allowed_model_ids = record.storage_id.model_ids.ids

    @api.depends("res_model")
    def _compute_model_id(self):
        for record in self:
            if not record.res_model:
                record.model_id = False
                continue
            record.model_id = self.env["ir.model"].search(
                [("model", "=", record.res_model)]
            )

    def _inverse_model_id(self):
        for record in self:
            record.res_model = record.model_id.model

    @api.depends("res_model", "res_id")
    def _compute_record_ref(self):
        for record in self:
            record.record_ref = False
            if record.res_model and record.res_id:
                record.record_ref = "{},{}".format(record.res_model, record.res_id)

    @api.depends("name", "complete_name")
    def _compute_display_name(self):
        if not self.env.context.get("directory_short_name", False):
            return super()._compute_display_name()
        for record in self:
            record.display_name = record.name

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
    def _search(
        self,
        args,
        offset=0,
        limit=None,
        order=None,
        count=False,
        access_rights_uid=None,
    ):
        result = super(DmsDirectory, self)._search(
            args, offset, limit, order, False, access_rights_uid
        )
        if result:
            directory_ids = set(result)
            if self.env.user.has_group("base.group_portal"):
                exclude_ids = self._get_ids_without_access_groups("read")
                directory_ids -= set(exclude_ids)
                return directory_ids
        return result

    @api.model
    def _search_starred(self, operator, operand):
        if operator == "=" and operand:
            return [("user_star_ids", "in", [self.env.uid])]
        return [("user_star_ids", "not in", [self.env.uid])]

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
                record.storage_id = record.root_storage_id
            else:
                record.storage_id = record.parent_id.storage_id

    @api.depends("user_star_ids")
    def _compute_starred(self):
        for record in self:
            record.starred = self.env.user in record.user_star_ids

    @api.depends("child_directory_ids")
    def _compute_count_directories(self):
        for record in self:
            directories = len(record.child_directory_ids)
            record.count_directories = directories
            record.count_directories_title = _("%s Subdirectories") % directories

    @api.depends("file_ids")
    def _compute_count_files(self):
        for record in self:
            files = len(record.file_ids)
            record.count_files = files
            record.count_files_title = _("%s Files") % files

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

    @api.depends("inherit_group_ids", "parent_path")
    def _compute_groups(self):
        records = self.filtered(lambda record: record.parent_path)
        paths = [list(map(int, rec.parent_path.split("/")[:-1])) for rec in records]
        ids = paths and set(functools.reduce(operator.concat, paths)) or []
        read = self.browse(ids).read(["inherit_group_ids", "group_ids"])
        data = {entry.pop("id"): entry for entry in read}
        for record in records:
            complete_group_ids = set()
            for directory_id in reversed(
                list(map(int, record.parent_path.split("/")[:-1]))
            ):
                if directory_id in data:
                    complete_group_ids |= set(data[directory_id].get("group_ids", []))
                    if not data[directory_id].get("inherit_group_ids"):
                        break
            record.update({"complete_group_ids": [(6, 0, list(complete_group_ids))]})
        for record in self - records:
            if record.parent_id and record.inherit_group_ids:
                complete_groups = record.parent_id.complete_group_ids
                record.complete_group_ids = record.group_ids | complete_groups
            else:
                record.complete_group_ids = record.group_ids

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

    @api.model
    def get_alias_model_name(self, vals):
        return vals.get("alias_model", "dms.directory")

    def get_alias_values(self):
        values = super().get_alias_values()
        values["alias_defaults"] = {"parent_id": self.id}
        return values

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        custom_values = custom_values if custom_values is not None else {}
        parent_directory_id = custom_values.get("parent_id", None)
        parent_directory = self.sudo().browse(parent_directory_id)
        if not parent_directory_id or not parent_directory.exists():
            raise ValueError("No directory could be found!")
        if parent_directory.alias_process == "files":
            parent_directory._process_message(msg_dict)
            return parent_directory
        names = parent_directory.child_directory_ids.mapped("name")
        subject = slugify(msg_dict.get("subject", _("Alias-Mail-Extraction")))
        defaults = dict(
            {"name": unique_name(subject, names, escape_suffix=True)}, **custom_values
        )
        directory = super().message_new(msg_dict, custom_values=defaults)
        directory._process_message(msg_dict)
        return directory

    def message_update(self, msg_dict, update_vals=None):
        self._process_message(msg_dict, extra_values=update_vals)
        return super().message_update(msg_dict, update_vals=update_vals)

    def _process_message(self, msg_dict, extra_values=False):
        names = self.sudo().file_ids.mapped("name")
        for attachment in msg_dict["attachments"]:
            uname = unique_name(attachment.fname, names, escape_suffix=True)
            self.env["dms.file"].sudo().create(
                {
                    "content": base64.b64encode(attachment.content),
                    "directory_id": self.id,
                    "name": uname,
                }
            )
            names.append(uname)

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
        if any(key in vals for key in ["group_ids", "inherit_group_ids"]):
            with self.env.norecompute():
                res = super(DmsDirectory, self).write(vals)
                domain = [("id", "child_of", self.ids)]
                records = self.sudo().search(domain)
                records.modified(["group_ids"])
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
