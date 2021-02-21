# Copyright 2017-2019 MuK IT GmbH.
# Copyright 2020 Creu Blanca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64
import logging
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
    group_ids = fields.Many2many(
        comodel_name="res.groups",
        relation="dms_directory_group_rel",
        column1="did",
        column2="gid",
        string="Group ids",
    )
    read_group_ids = fields.Many2many(
        comodel_name="res.groups",
        relation="dms_directory_read_group_rel",
        column1="did",
        column2="rgid",
        string="Read group ids",
    )
    complete_group_ids = fields.Many2many(
        comodel_name="res.groups",
        relation="dms_directory_complete_group_rel",
        column1="did",
        column2="cgid",
        string="Complete Group ids",
    )
    complete_read_group_ids = fields.Many2many(
        comodel_name="res.groups",
        relation="dms_directory_complete_read_group_rel",
        column1="did",
        column2="crgid",
        string="Complete Read group ids",
    )
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

    @api.model
    def _selection_target_model(self):
        models = self.env["ir.model"].search([])
        return [(model.model, model.name) for model in models]

    record_mail_followers_sync = fields.Boolean(
        string="Record mail followers sync", default=False
    )
    record_ref = fields.Reference(
        string="Record reference",
        selection="_selection_target_model",
        compute="_compute_record_ref",
        inverse="_inverse_record_ref",
    )
    record_ref_mail_follower_ids = fields.One2many(
        comodel_name="mail.followers",
        inverse_name="dms_directory_id",
        string="Record ref mail follower ids",
        readonly=True,
    )
    record_ref_message_partner_ids = fields.Many2many(
        comodel_name="res.partner",
        string="Record Followers (Partners)",
        compute_sudo="_get_followers",
        store=True,
    )
    storage_id_save_type = fields.Selection(related="storage_id.save_type", store=False)
    permission_write = fields.Boolean(
        compute="_compute_permissions_write", string="Write Access", store=False
    )
    permission_unlink = fields.Boolean(
        compute="_compute_permissions_unlink", string="Delete Access", store=False
    )

    @api.depends("res_model", "res_id")
    def _compute_record_ref(self):
        for preview in self:
            if preview.res_model:
                preview.record_ref = "{},{}".format(
                    preview.res_model, preview.res_id or 0
                )
            else:
                preview.record_ref = False

    def _inverse_record_ref(self):
        for preview in self:
            if preview.record_ref:
                preview.res_id = preview.record_ref.id

    def _compute_permissions_write(self):
        for item in self:
            if item.check_access_rights("write", False):
                item.permission_write = True
            else:
                item.permission_write = False

    def _compute_permissions_unlink(self):
        for item in self:
            if item.check_access_rights("unlink", False):
                item.permission_unlink = True
            else:
                item.permission_unlink = False

    @api.depends("record_ref_mail_follower_ids")
    def _get_followers(self):
        for item in self:
            field_name = "record_ref_message_partner_ids"
            item[field_name] = False
            if item[field_name]:
                item[field_name] = item[field_name].mapped("partner_id")

    def sync_res_model_records(self):
        self.ensure_one()
        if self.res_model and not self.res_id:
            res_id = (
                self.env["ir.attachment"]
                .sudo()
                .search([("res_model", "=", self.res_model), ("type", "=", "binary")])
                .mapped("res_id")
            )
            if res_id:
                items = self.env[self.res_model].sudo().search([("id", "in", res_id)])
                for item in items:
                    val_sync = self.record_mail_followers_sync
                    dms_directory = self.env["dms.directory"].create(
                        {
                            "name": item.display_name,
                            "model_id": self.model_id.id,
                            "res_model": self.res_model,
                            "res_id": item.id,
                            "parent_id": self.id,
                            "storage_id": self.storage_id.id,
                            "record_mail_followers_sync": val_sync,
                        }
                    )
                    dms_directory.sync_res_model_record()

    def sync_res_model_record(self):
        self.ensure_one()
        if self.res_model and self.res_id:
            attachments = (
                self.env["ir.attachment"]
                .sudo()
                .search(
                    [
                        ("res_model", "=", self.res_model),
                        ("res_id", "=", self.res_id),
                        ("type", "=", "binary"),
                    ]
                )
            )
            for attachment in attachments:
                attachment._dms_operations()

    def define_record_ref_mail_follower_ids(self):
        self.ensure_one()
        if self.res_model and self.res_id and self.record_mail_followers_sync:
            followers = (
                self.env["mail.followers"]
                .sudo()
                .search(
                    [("res_model", "=", self.res_model), ("res_id", "=", self.res_id)]
                )
            )
            followers.write({"dms_directory_id": self.id})

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
                    while (
                        directory_item.parent_id.check_access_rights("read", False)
                        and directory_item.parent_id
                    ):
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
            while (
                current_directory.parent_id
                and current_directory.parent_id.check_access_rights("read", False)
                and not stop
            ):
                if current_directory.access_token == access_token:
                    stop = False
                else:
                    directories.append(current_directory.parent_id)
                current_directory = current_directory.parent_id
        else:
            while (
                current_directory.parent_id
                and current_directory.parent_id.check_access_rights("read", False)
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
                and current_directory.parent_id.check_access_rights("read", False)
            ):
                current_directory = current_directory.parent_id

            if current_directory.id not in ids:
                ids.append(current_directory.id)

        return ids

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

    def _set_complete_group_ids(self, field_name):
        for item in self:
            group_ids = item[field_name]
            complete_field = "complete_%s" % field_name
            if item.inherit_group_ids:
                group_ids += item.parent_id[complete_field]
            item[complete_field] = group_ids
            # update childs
            if item.child_directory_ids:
                childs = item.child_directory_ids.filtered(
                    lambda x: x.inherit_group_ids
                )
                for child in childs:
                    child[complete_field] = child[field_name] + item[complete_field]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("root_storage_id", False):
                vals["storage_id"] = vals["root_storage_id"]
            if vals.get("parent_id", False):
                parent = self.browse([vals["parent_id"]])
                data = next(iter(parent.sudo().read(["storage_id"])), {})
                vals["storage_id"] = self._convert_to_write(data).get("storage_id")
        res = super().create(vals_list)
        res._set_complete_group_ids("group_ids")
        res._set_complete_group_ids("read_group_ids")
        return res

    def write(self, vals):
        # Groups part
        res = super().write(vals)
        if any(
            key in vals for key in ["inherit_group_ids", "group_ids", "read_group_ids"]
        ):
            self._set_complete_group_ids("group_ids")
            self._set_complete_group_ids("read_group_ids")

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
