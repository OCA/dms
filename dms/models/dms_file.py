# Copyright 2020 Antoni Romera
# Copyright 2017-2019 MuK IT GmbH
# Copyright 2021 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64
import hashlib
import json
import logging
from collections import defaultdict

from odoo import _, api, fields, models, tools
from odoo.exceptions import ValidationError
from odoo.osv import expression
from odoo.tools import consteq, human_size
from odoo.tools.mimetypes import guess_mimetype

from ..tools import file

_logger = logging.getLogger(__name__)


class File(models.Model):

    _name = "dms.file"
    _description = "File"

    _inherit = [
        "portal.mixin",
        "dms.security.mixin",
        "dms.mixins.thumbnail",
        "mail.thread",
        "mail.activity.mixin",
        "abstract.dms.mixin",
    ]

    _order = "name asc"

    # ----------------------------------------------------------
    # Database
    # ----------------------------------------------------------

    active = fields.Boolean(
        string="Archived",
        default=True,
        help="If a file is set to archived, it is not displayed, but still exists.",
    )

    directory_id = fields.Many2one(
        comodel_name="dms.directory",
        string="Directory",
        domain="[('permission_create', '=', True)]",
        context="{'dms_directory_show_path': True}",
        ondelete="restrict",
        auto_join=True,
        required=True,
        index=True,
    )
    # Override acording to defined in AbstractDmsMixin
    storage_id = fields.Many2one(
        related="directory_id.storage_id", readonly=True, store=True, prefetch=False,
    )

    path_names = fields.Char(
        compute="_compute_path",
        compute_sudo=True,
        string="Path Names",
        readonly=True,
        store=False,
    )

    path_json = fields.Text(
        compute="_compute_path",
        compute_sudo=True,
        string="Path Json",
        readonly=True,
        store=False,
    )

    tag_ids = fields.Many2many(
        comodel_name="dms.tag",
        relation="dms_file_tag_rel",
        column1="fid",
        column2="tid",
        string="Tags",
    )

    content = fields.Binary(
        compute="_compute_content",
        inverse="_inverse_content",
        string="Content",
        attachment=False,
        prefetch=False,
        required=True,
        store=False,
    )

    extension = fields.Char(
        compute="_compute_extension", string="Extension", readonly=True, store=True
    )

    res_mimetype = fields.Char(
        compute="_compute_mimetype", string="Type", readonly=True, store=True
    )

    size = fields.Integer(string="Size", readonly=True)

    checksum = fields.Char(string="Checksum/SHA1", readonly=True, size=40, index=True)

    content_binary = fields.Binary(
        string="Content Binary", attachment=False, prefetch=False, invisible=True
    )

    save_type = fields.Char(
        compute="_compute_save_type",
        string="Current Save Type",
        invisible=True,
        prefetch=False,
    )

    migration = fields.Char(
        compute="_compute_migration",
        string="Migration Status",
        readonly=True,
        prefetch=False,
        compute_sudo=True,
    )
    require_migration = fields.Boolean(
        compute="_compute_migration", store=True, compute_sudo=True
    )

    content_file = fields.Binary(
        attachment=True, string="Content File", prefetch=False, invisible=True
    )

    # Extend inherited field(s)
    image_1920 = fields.Image(compute="_compute_image_1920", store=True, readonly=False)

    @api.depends("res_mimetype", "content")
    def _compute_image_1920(self):
        """Provide thumbnail automatically if possible."""
        for one in self.filtered("res_mimetype"):
            if one.res_mimetype.startswith("image/"):
                one.image_1920 = one.content

    def check_access_rule(self, operation):
        self.mapped("directory_id").check_access_rule(operation)
        return super().check_access_rule(operation)

    def _compute_access_url(self):
        super()._compute_access_url()
        for item in self:
            item.access_url = "/my/dms/file/%s/download" % (item.id)

    def check_access_token(self, access_token=False):
        res = False
        if access_token:
            if self.access_token and consteq(self.access_token, access_token):
                return True
            else:
                items = (
                    self.env["dms.directory"]
                    .sudo()
                    .search([("access_token", "=", access_token)])
                )
                if items:
                    item = items[0]
                    if self.directory_id.id == item.id:
                        return True
                    else:
                        directory_item = self.directory_id
                        while directory_item.parent_id:
                            if directory_item.id == self.directory_id.id:
                                return True
                            directory_item = directory_item.parent_id
                        # Fix last level
                        if directory_item.id == self.directory_id.id:
                            return True
        return res

    res_model = fields.Char(
        string="Linked attachments model", related="directory_id.res_model"
    )
    res_id = fields.Integer(
        string="Linked attachments record ID", related="directory_id.res_id"
    )
    attachment_id = fields.Many2one(
        comodel_name="ir.attachment",
        string="Attachment File",
        prefetch=False,
        invisible=True,
        ondelete="cascade",
    )

    def get_human_size(self):
        return human_size(self.size)

    # ----------------------------------------------------------
    # Helper
    # ----------------------------------------------------------

    @api.model
    def _get_checksum(self, binary):
        return hashlib.sha1(binary or b"").hexdigest()

    @api.model
    def _get_content_inital_vals(self):
        return {"content_binary": False, "content_file": False}

    def _update_content_vals(self, vals, binary):
        new_vals = vals.copy()
        new_vals.update(
            {
                "checksum": self._get_checksum(binary),
                "size": binary and len(binary) or 0,
            }
        )
        if self.storage_id.save_type in ["file", "attachment"]:
            new_vals["content_file"] = self.content
        else:
            new_vals["content_binary"] = self.content and binary
        return new_vals

    @api.model
    def _get_binary_max_size(self):
        return int(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("dms.binary_max_size", default=25)
        )

    @api.model
    def _get_forbidden_extensions(self):
        get_param = self.env["ir.config_parameter"].sudo().get_param
        extensions = get_param("dms.forbidden_extensions", default="")
        return [extension.strip() for extension in extensions.split(",")]

    def _get_icon_placeholder_name(self):
        return self.extension and "file_%s.svg" % self.extension or ""

    # ----------------------------------------------------------
    # Actions
    # ----------------------------------------------------------

    def action_migrate(self, logging=True):
        record_count = len(self)
        index = 1
        for dms_file in self:
            if logging:
                info = (index, record_count, dms_file.migration)
                _logger.info(_("Migrate File %s of %s [ %s ]") % info)
                index += 1
            dms_file.write({"content": dms_file.with_context({}).content})

    def action_save_onboarding_file_step(self):
        self.env.user.company_id.set_onboarding_step_done(
            "documents_onboarding_file_state"
        )

    # ----------------------------------------------------------
    # SearchPanel
    # ----------------------------------------------------------

    @api.model
    def _search_panel_directory(self, **kwargs):
        search_domain = (kwargs.get("search_domain", []),)
        category_domain = kwargs.get("category_domain", [])
        if category_domain and len(category_domain):
            return "=", category_domain[0][2]
        if search_domain and len(search_domain):
            for domain in search_domain[0]:
                if domain[0] == "directory_id":
                    return domain[1], domain[2]
        return None, None

    @api.model
    def _search_panel_domain(self, field, operator, directory_id, comodel_domain=False):
        if not comodel_domain:
            comodel_domain = []
        files_ids = self.search([("directory_id", operator, directory_id)]).ids
        return expression.AND([comodel_domain, [(field, "in", files_ids)]])

    @api.model
    def search_panel_select_range(self, field_name, **kwargs):
        operator, directory_id = self._search_panel_directory(**kwargs)
        if directory_id and field_name == "directory_id":
            domain = [("parent_id", operator, directory_id)]
            values = (
                self.env["dms.directory"]
                .with_context(directory_short_name=True)
                .search_read(domain, ["display_name", "parent_id"])
            )
            return {
                "parent_field": "parent_id",
                "values": values if len(values) > 1 else [],
            }
        context = {}
        if field_name == "directory_id":
            context["directory_short_name"] = True
        return super(File, self.with_context(**context)).search_panel_select_range(
            field_name, **kwargs
        )

    @api.model
    def search_panel_select_multi_range(self, field_name, **kwargs):
        operator, directory_id = self._search_panel_directory(**kwargs)
        if field_name == "tag_ids":
            sql_query = """
                SELECT t.name AS name, t.id AS id, c.name AS group_name,
                    c.id AS group_id, COUNT(r.fid) AS count
                FROM dms_tag t
                JOIN dms_category c ON t.category_id = c.id
                LEFT JOIN dms_file_tag_rel r ON t.id = r.tid
                WHERE %(filter_by_file_ids)s IS FALSE OR r.fid = ANY(%(file_ids)s)
                GROUP BY c.name, c.id, t.name, t.id
                ORDER BY c.name, c.id, t.name, t.id;
            """
            file_ids = []
            if directory_id:
                file_ids = self.search([("directory_id", operator, directory_id)]).ids
            self.env.cr.execute(
                sql_query,
                {"file_ids": file_ids, "filter_by_file_ids": bool(directory_id)},
            )
            return self.env.cr.dictfetchall()
        if directory_id and field_name in ["directory_id", "category_id"]:
            comodel_domain = kwargs.pop("comodel_domain", [])
            directory_comodel_domain = self._search_panel_domain(
                "file_ids", operator, directory_id, comodel_domain
            )
            return super(
                File, self.with_context(directory_short_name=True)
            ).search_panel_select_multi_range(
                field_name, comodel_domain=directory_comodel_domain, **kwargs
            )
        return super(
            File, self.with_context(directory_short_name=True)
        ).search_panel_select_multi_range(field_name, **kwargs)

    # ----------------------------------------------------------
    # Read
    # ----------------------------------------------------------

    @api.depends("name", "directory_id", "directory_id.parent_path")
    def _compute_path(self):
        model = self.env["dms.directory"]
        for record in self:
            record_name = record.display_name or _("Unnamed")
            path_names = [record_name]
            path_json = [
                {
                    "model": record._name,
                    "name": record_name,
                    "id": isinstance(record.id, int) and record.id or 0,
                }
            ]
            current_dir = record.directory_id
            while current_dir:
                path_names.insert(0, current_dir.name)
                path_json.insert(
                    0,
                    {
                        "model": model._name,
                        "name": current_dir.name,
                        "id": current_dir.id,
                    },
                )
                current_dir = current_dir.parent_id
            record.update(
                {
                    "path_names": "/".join(path_names),
                    "path_json": json.dumps(path_json),
                }
            )

    @api.depends("name")
    def _compute_extension(self):
        for record in self:
            record.extension = file.guess_extension(record.name)

    @api.depends("content")
    def _compute_mimetype(self):
        for record in self:
            record.res_mimetype = guess_mimetype(base64.b64decode(record.content or ""))

    @api.depends("content_binary", "content_file", "attachment_id")
    def _compute_content(self):
        bin_size = self.env.context.get("bin_size", False)
        for record in self:
            if record.content_file:
                context = {"human_size": True} if bin_size else {"base64": True}
                record.content = record.with_context(context).content_file
            elif record.content_binary:
                record.content = (
                    record.content_binary
                    if bin_size
                    else base64.b64encode(record.content_binary)
                )
            elif record.attachment_id:
                context = {"human_size": True} if bin_size else {"base64": True}
                record.content = record.with_context(context).attachment_id.datas

    @api.depends("content_binary", "content_file")
    def _compute_save_type(self):
        for record in self:
            if record.content_file:
                record.save_type = "file"
            else:
                record.save_type = "database"

    @api.depends("storage_id", "storage_id.save_type")
    def _compute_migration(self):
        storage_model = self.env["dms.storage"]
        save_field = storage_model._fields["save_type"]
        values = save_field._description_selection(self.env)
        selection = {value[0]: value[1] for value in values}
        for record in self:
            storage_type = record.storage_id.save_type
            if storage_type == "attachment" or storage_type == record.save_type:
                record.migration = selection.get(storage_type)
                record.require_migration = False
            else:
                storage_label = selection.get(storage_type)
                file_label = selection.get(record.save_type)
                record.migration = "{} > {}".format(file_label, storage_label)
                record.require_migration = True

    # ----------------------------------------------------------
    # View
    # ----------------------------------------------------------

    @api.onchange("category_id")
    def _change_category(self):
        res = {"domain": {"tag_ids": [("category_id", "=", False)]}}
        if self.category_id:
            res.update(
                {
                    "domain": {
                        "tag_ids": [
                            "|",
                            ("category_id", "=", False),
                            ("category_id", "child_of", self.category_id.id),
                        ]
                    }
                }
            )
        tags = self.tag_ids.filtered(
            lambda rec: not rec.category_id or rec.category_id == self.category_id
        )
        self.tag_ids = tags
        return res

    # ----------------------------------------------------------
    # Constrains
    # ----------------------------------------------------------

    @api.constrains("storage_id", "res_model", "res_id")
    def _check_storage_id_attachment_res_model(self):
        for record in self:
            if record.storage_id.save_type == "attachment" and not (
                record.res_model and record.res_id
            ):
                raise ValidationError(
                    _("A file must have model and resource ID in attachment storage.")
                )

    @api.constrains("name")
    def _check_name(self):
        for record in self:
            if not file.check_name(record.name):
                raise ValidationError(_("The file name is invalid."))
            files = record.sudo().directory_id.file_ids.name_get()
            if list(
                filter(
                    lambda file: file[1] == record.name and file[0] != record.id, files
                )
            ):
                raise ValidationError(_("A file with the same name already exists."))

    @api.constrains("extension")
    def _check_extension(self):
        for record in self:
            if (
                record.extension
                and record.extension in self._get_forbidden_extensions()
            ):
                raise ValidationError(_("The file has a forbidden file extension."))

    @api.constrains("size")
    def _check_size(self):
        for record in self:
            if record.size and record.size > self._get_binary_max_size() * 1024 * 1024:
                raise ValidationError(
                    _("The maximum upload size is %s MB).")
                    % self._get_binary_max_size()
                )

    # ----------------------------------------------------------
    # Create, Update, Delete
    # ----------------------------------------------------------

    def _inverse_content(self):
        updates = defaultdict(set)
        for record in self:
            values = self._get_content_inital_vals()
            binary = base64.b64decode(record.content or "")
            values = record._update_content_vals(values, binary)
            updates[tools.frozendict(values)].add(record.id)
        with self.env.norecompute():
            for vals, ids in updates.items():
                self.browse(ids).write(dict(vals))

    def _create_model_attachment(self, vals):
        res_vals = vals.copy()
        if "directory_id" in res_vals:
            directory_id = res_vals["directory_id"]
        elif self.env.context.get("active_id"):
            directory_id = self.env.context.get("active_id")
        elif self.env.context.get("default_directory_id"):
            directory_id = self.env.context.get("default_directory_id")
        directory = self.env["dms.directory"].browse(directory_id)
        if directory.res_model and directory.res_id:
            attachment = (
                self.env["ir.attachment"]
                .with_context(dms_file=True)
                .create(
                    {
                        "name": vals["name"],
                        "datas": vals["content"],
                        "res_model": directory.res_model,
                        "res_id": directory.res_id,
                    }
                )
            )
            res_vals["attachment_id"] = attachment.id
            res_vals["res_model"] = attachment.res_model
            res_vals["res_id"] = attachment.res_id
            del res_vals["content"]
        return res_vals

    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or [])
        if "directory_id" in default:
            model = self.env["dms.directory"]
            directory = model.browse(default["directory_id"])
            names = directory.sudo().file_ids.mapped("name")
        else:
            names = self.sudo().directory_id.file_ids.mapped("name")
        default.update({"name": file.unique_name(self.name, names, self.extension)})
        return super(File, self).copy(default)

    @api.model_create_multi
    def create(self, vals_list):
        new_vals_list = []
        for vals in vals_list:
            if "attachment_id" not in vals:
                vals = self._create_model_attachment(vals)
            new_vals_list.append(vals)
        return super(File, self).create(new_vals_list)

    # ----------------------------------------------------------
    # Locking fields and functions
    # ----------------------------------------------------------

    locked_by = fields.Many2one(comodel_name="res.users", string="Locked by")

    is_locked = fields.Boolean(compute="_compute_locked", string="Locked")

    is_lock_editor = fields.Boolean(compute="_compute_locked", string="Editor")

    # ----------------------------------------------------------
    # Locking
    # ----------------------------------------------------------

    def lock(self):
        self.write({"locked_by": self.env.uid})

    def unlock(self):
        self.write({"locked_by": None})

    # ----------------------------------------------------------
    # Read, View
    # ----------------------------------------------------------

    @api.depends("locked_by")
    def _compute_locked(self):
        for record in self:
            if record.locked_by.exists():
                record.update(
                    {
                        "is_locked": True,
                        "is_lock_editor": record.locked_by.id == record.env.uid,
                    }
                )
            else:
                record.update({"is_locked": False, "is_lock_editor": False})
