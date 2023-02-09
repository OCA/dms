# Copyright 2017-2019 MuK IT GmbH.
# Copyright 2020 Creu Blanca
# Copyright 2021 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64
import logging
from collections import defaultdict

from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError, ValidationError
from odoo.osv.expression import OR
from odoo.tools import consteq

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
        "abstract.dms.mixin",
    ]

    _rec_name = "complete_name"
    _order = "complete_name"

    _parent_store = True
    _parent_name = "parent_id"
    _directory_field = _parent_name

    parent_path = fields.Char(index=True)
    is_root_directory = fields.Boolean(
        string="Is Root Directory",
        default=False,
        help="""Indicates if the directory is a root directory.
        A root directory has a settings object, while a directory with a set
        parent inherits the settings form its parent.""",
    )

    # Override acording to defined in AbstractDmsMixin
    storage_id = fields.Many2one(
        compute="_compute_storage_id",
        compute_sudo=True,
        readonly=False,
        comodel_name="dms.storage",
        string="Storage",
        ondelete="restrict",
        auto_join=True,
        store=True,
    )
    parent_id = fields.Many2one(
        comodel_name="dms.directory",
        string="Parent Directory",
        domain="[('permission_create', '=', True)]",
        ondelete="restrict",
        # Access to a directory doesn't necessarily mean access its parent, so
        # prefetching this field could lead to misleading access errors
        prefetch=False,
        index=True,
        store=True,
        readonly=False,
        compute="_compute_parent_id",
        copy=True,
        default=lambda self: self._default_parent_id(),
    )

    def _default_parent_id(self):
        context = self.env.context
        if context.get("active_model") == self._name and context.get("active_id"):
            return context["active_id"]
        else:
            return False

    group_ids = fields.Many2many(
        comodel_name="dms.access.group",
        relation="dms_directory_groups_rel",
        column1="aid",
        column2="gid",
        string="Groups",
    )
    complete_group_ids = fields.Many2many(
        comodel_name="dms.access.group",
        relation="dms_directory_complete_groups_rel",
        column1="aid",
        column2="gid",
        string="Complete Groups",
        compute="_compute_groups",
        readonly=True,
        store=True,
        compute_sudo=True,
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

    size = fields.Float(compute="_compute_size", string="Size")

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

    @api.model
    def _get_domain_by_access_groups(self, operation):
        """Special rules for directories."""
        self_filter = [
            ("storage_id_inherit_access_from_parent_record", "=", False),
            ("id", "inselect", self._get_access_groups_query(operation)),
        ]
        # Upstream only filters by parent directory
        result = super()._get_domain_by_access_groups(operation)
        if operation == "create":
            # When creating, I need create access in parent directory, or
            # self-create permission if it's a root directory
            result = OR(
                [
                    [("is_root_directory", "=", False)] + result,
                    [("is_root_directory", "=", True)] + self_filter,
                ]
            )
        else:
            # In other operations, I only need self access
            result = self_filter
        return result

    def _compute_access_url(self):
        super()._compute_access_url()
        for item in self:
            item.access_url = "/my/dms/directory/%s" % (item.id)

    def check_access_token(self, access_token=False):
        res = False
        if access_token:
            items = (
                self.env["dms.directory"]
                .sudo()
                .search([("access_token", "=", access_token)])
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
        directories = []
        current_directory = self
        while current_directory:
            directories.insert(0, current_directory)
            if (
                (
                    access_token
                    and current_directory.access_token
                    and consteq(current_directory.access_token, access_token)
                )
                or not access_token
                and current_directory.check_access_rights("read")
            ):
                return directories
            current_directory = current_directory.parent_id
        if access_token:
            # Reaching here means we didn't find the directory accessible by this token
            return [self]
        return directories

    def _get_own_root_directories(self):
        res = self.env["dms.directory"].search_read(
            [("is_hidden", "=", False)], ["parent_id"]
        )
        all_ids = [value["id"] for value in res]
        res_ids = []
        for item in res:
            if not item["parent_id"] or item["parent_id"][0] not in all_ids:
                res_ids.append(item["id"])
        return res_ids

    allowed_model_ids = fields.Many2many(
        related="storage_id.model_ids",
        comodel_name="ir.model",
    )
    model_id = fields.Many2one(
        comodel_name="ir.model",
        domain="[('id', 'in', allowed_model_ids)]",
        compute="_compute_model_id",
        inverse="_inverse_model_id",
        string="Model",
        store=True,
    )
    storage_id_save_type = fields.Selection(
        related="storage_id.save_type",
        related_sudo=True,
        readonly=True,
        store=False,
        prefetch=False,
    )
    storage_id_inherit_access_from_parent_record = fields.Boolean(
        related="storage_id.inherit_access_from_parent_record",
        related_sudo=True,
        auto_join=True,
        store=True,
    )

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
    def _search_starred(self, operator, operand):
        if operator == "=" and operand:
            return [("user_star_ids", "in", [self.env.uid])]
        return [("user_star_ids", "not in", [self.env.uid])]

    @api.depends("name", "parent_id.complete_name")
    def _compute_complete_name(self):
        for category in self:
            if category.parent_id:
                category.complete_name = "{} / {}".format(
                    category.parent_id.complete_name,
                    category.name,
                )
            else:
                category.complete_name = category.name

    @api.depends("parent_id")
    def _compute_storage_id(self):
        for record in self:
            if record.parent_id:
                record.storage_id = record.parent_id.storage_id
            else:
                # HACK: Not needed in v14 due to odoo/odoo#64359
                record.storage_id = record.storage_id

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
            count = (
                self.search_count([("id", "child_of", record.id)]) if record.id else 0
            )
            record.count_total_directories = count - 1 if count > 0 else 0

    def _compute_count_total_files(self):
        model = self.env["dms.file"]
        for record in self:
            # Prevent error in some NewId cases
            record.count_total_files = (
                model.search_count([("directory_id", "child_of", record.id)])
                if record.id
                else 0
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
                domain=[("directory_id", "child_of", record.id)],
                fields=["size"],
            )
            record.size = sum(rec.get("size", 0) for rec in recs)

    @api.depends(
        "group_ids",
        "inherit_group_ids",
        "parent_id.complete_group_ids",
        "parent_path",
    )
    def _compute_groups(self):
        """Get all DMS security groups affecting this directory."""
        for one in self:
            groups = one.group_ids
            if one.inherit_group_ids:
                groups |= one.parent_id.complete_group_ids
            self.complete_group_ids = groups

    # ----------------------------------------------------------
    # View
    # ----------------------------------------------------------

    @api.depends("is_root_directory")
    def _compute_parent_id(self):
        for record in self:
            if record.is_root_directory:
                record.parent_id = None
            else:
                # HACK: Not needed in v14 due to odoo/odoo#64359
                record.parent_id = record.parent_id

    @api.depends("category_id")
    def _compute_tags(self):
        for record in self:
            tags = record.tag_ids.filtered(
                lambda rec: not rec.category_id or rec.category_id == record.category_id
            )
            record.tag_ids = tags

    @api.onchange("storage_id")
    def _onchange_storage_id(self):
        for record in self:
            if (
                record.storage_id.save_type == "attachment"
                and record.storage_id.inherit_access_from_parent_record
            ):
                record.group_ids = False

    @api.onchange("model_id")
    def _onchange_model_id(self):
        self._inverse_model_id()

    # ----------------------------------------------------------
    # Constrains
    # ----------------------------------------------------------

    @api.constrains("parent_id")
    def _check_directory_recursion(self):
        if not self._check_recursion():
            raise ValidationError(_("Error! You cannot create recursive directories."))
        return True

    @api.constrains("storage_id", "model_id")
    def _check_storage_id_attachment_model_id(self):
        for record in self:
            if record.storage_id.save_type != "attachment":
                continue
            if not record.model_id:
                raise ValidationError(
                    _("A directory has to have model in attachment storage.")
                )
            if not record.is_root_directory and not record.res_id:
                raise ValidationError(
                    _("This directory needs to be associated to a record.")
                )

    @api.constrains("is_root_directory", "storage_id")
    def _check_directory_storage(self):
        for record in self:
            if record.is_root_directory and not record.storage_id:
                raise ValidationError(_("A root directory has to have a storage."))

    @api.constrains("is_root_directory", "parent_id")
    def _check_directory_parent(self):
        for record in self:
            if record.is_root_directory and record.parent_id:
                raise ValidationError(
                    _("A directory can't be a root and have a parent directory.")
                )
            if not record.is_root_directory and not record.parent_id:
                raise ValidationError(_("A directory has to have a parent directory."))

    @api.constrains("name")
    def _check_name(self):
        for record in self:
            if self.env.context.get("check_name", True) and not check_name(record.name):
                raise ValidationError(_("The directory name is invalid."))
            if record.is_root_directory:
                childs = record.sudo().storage_id.root_directory_ids.name_get()
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
        if "parent_id" in default:
            parent_directory = self.browse(default["parent_id"])
            names = parent_directory.sudo().child_directory_ids.mapped("name")
        elif self.is_root_directory:
            names = self.sudo().storage_id.root_directory_ids.mapped("name")
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
            if vals.get("parent_id", False):
                parent = self.browse([vals["parent_id"]])
                data = next(iter(parent.sudo().read(["storage_id"])), {})
                vals["storage_id"] = self._convert_to_write(data).get("storage_id")
        # Hack to prevent error related to mail_message parent not exists in some cases
        ctx = dict(self.env.context).copy()
        ctx.update({"default_parent_id": False})
        res = super(DmsDirectory, self.with_context(ctx)).create(vals_list)
        return res

    def write(self, vals):
        if vals.get("storage_id"):
            for item in self:
                if item.storage_id.id != vals["storage_id"]:
                    raise UserError(_("It is not possible to change the storage."))
        if vals.get("parent_id"):
            parent = self.browse([vals["parent_id"]])
            for item in self:
                if item.parent_id.storage_id != parent.storage_id:
                    raise UserError(
                        _("It is not possible to change parent to other storage.")
                    )
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
        return res

    def unlink(self):
        """Custom cascade unlink.

        Cannot rely on DB backend's cascade because subfolder and subfile unlinks
        must check custom permissions implementation.
        """
        self.file_ids.unlink()
        if self.child_directory_ids:
            self.child_directory_ids.unlink()
        return super().unlink()
