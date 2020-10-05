# Copyright 2020 Antoni Romera
# Copyright 2017-2019 MuK IT GmbH
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64
import hashlib
import json
import logging
import mimetypes
from collections import defaultdict

from odoo import SUPERUSER_ID, _, api, fields, models, tools
from odoo.exceptions import AccessError, ValidationError
from odoo.osv import expression
from odoo.tools import human_size
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
    ]

    _order = "name asc"

    # ----------------------------------------------------------
    # Database
    # ----------------------------------------------------------

    name = fields.Char(string="Filename", required=True, index=True)

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

    storage_id = fields.Many2one(
        related="directory_id.storage_id",
        comodel_name="dms.storage",
        string="Storage",
        auto_join=True,
        readonly=True,
        store=True,
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

    path_names = fields.Char(
        compute="_compute_path", string="Path Names", readonly=True, store=False
    )

    path_json = fields.Text(
        compute="_compute_path", string="Path Json", readonly=True, store=False
    )

    color = fields.Integer(string="Color", default=0)

    category_id = fields.Many2one(
        comodel_name="dms.category",
        context="{'dms_category_show_path': True}",
        string="Category",
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
        compute="_compute_migration", store=True, compute_sudo=True,
    )

    content_file = fields.Binary(
        attachment=True, string="Content File", prefetch=False, invisible=True
    )

    def check_access_token(self, access_token=False):
        res = False
        if access_token:
            if self.access_token and self.access_token == access_token:
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

    def get_human_size(self):
        return human_size(self.size)

    def _get_share_url(self, redirect=False, signup_partner=False, pid=None):
        self.ensure_one()
        return "/my/dms/file/{}/download?access_token={}&db={}".format(
            self.id, self._portal_ensure_token(), self.env.cr.dbname,
        )

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
        if self.storage_id.save_type == "file":
            new_vals["content_file"] = self.content
        elif self.storage_id.save_type == "database":
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

    def _get_thumbnail_placeholder_name(self):
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
                {directory_where_clause}
                GROUP BY c.name, c.id, t.name, t.id
                ORDER BY c.name, c.id, t.name, t.id;
            """
            where_clause = ""
            params = []
            if directory_id:
                file_ids = self.search([("directory_id", operator, directory_id)]).ids
                if file_ids:
                    where_clause = "WHERE r.fid in %s"
                    params.append(tuple(file_ids))
                else:
                    where_clause = "WHERE 1 = 0"
            # pylint: disable=sql-injection
            final_query = sql_query.format(directory_where_clause=where_clause)
            self.env.cr.execute(final_query, params)
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
        data = {}
        for record in self:
            path_names = []
            path_json = []
            if record.directory_id.parent_path:
                for directory_id in reversed(
                    list(map(int, record.directory_id.parent_path.split("/")[:-1]))
                ):
                    if not directory_id:
                        break
                    if directory_id not in data:
                        data[directory_id] = model.browse(directory_id)
                    path_names.append(data[directory_id].name)
                    path_json.append(
                        {
                            "model": model._name,
                            "name": data[directory_id].name,
                            "id": directory_id,
                        }
                    )
            path_names.reverse()
            path_json.reverse()
            name = record.name_get()
            path_names.append(name[0][1])
            path_json.append(
                {
                    "model": record._name,
                    "name": name[0][1],
                    "id": isinstance(record.id, int) and record.id or 0,
                }
            )
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

    @api.depends("name", "content")
    def _compute_mimetype(self):
        for record in self:
            mimetype = record.name and mimetypes.guess_type(record.name)[0]
            if not mimetype and record.content:
                binary = base64.b64decode(record.with_context({}).content or "")
                mimetype = guess_mimetype(binary, default="application/octet-stream")
            record.res_mimetype = mimetype

    @api.depends("content_binary", "content_file")
    def _compute_content(self):
        bin_size = self.env.context.get("bin_size", False)
        for record in self:
            if record.content_file:
                context = {"human_size": True} if bin_size else {"base64": True}
                record.content = record.with_context(context).content_file
            else:
                record.content = base64.b64encode(record.content_binary)

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
            if storage_type != record.save_type:
                storage_label = selection.get(storage_type)
                file_label = selection.get(record.save_type)
                record.migration = "{} > {}".format(file_label, storage_label)
                record.require_migration = True
            else:
                record.migration = selection.get(storage_type)
                record.require_migration = False

    def read(self, fields=None, load="_classic_read"):
        self.check_directory_access("read", {}, True)
        return super(File, self).read(fields, load=load)

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
    # Security
    # ----------------------------------------------------------

    @api.model
    def _get_directories_from_database(self, file_ids):
        if not file_ids:
            return self.env["dms.directory"]
        return self.env["dms.file"].browse(file_ids).mapped("directory_id")

    @api.model
    def _read_group_process_groupby(self, gb, query):
        if self.env.user.id == SUPERUSER_ID:
            return super(File, self)._read_group_process_groupby(gb, query)
        directories = (
            self.env["dms.directory"].with_context(prefetch_fields=False).search([])
        )
        if directories:
            where_clause = '"{table}"."{field}" = ANY (VALUES {ids})'.format(
                table=self._table,
                field="directory_id",
                ids=", ".join(map(lambda id: "(%s)" % id, directories.ids)),
            )
            query.where_clause += [where_clause]
        else:
            query.where_clause += ["0=1"]
        return super(File, self)._read_group_process_groupby(gb, query)

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
        result = super(File, self)._search(
            args, offset, limit, order, False, access_rights_uid
        )
        if self.env.user.id == SUPERUSER_ID:
            return len(result) if count else result
        # Fix access files with share button (public)
        if self.env.user.has_group("base.group_public"):
            return len(result) if count else result
        # operations
        if not result:
            return 0 if count else []
        file_ids = set(result)
        directories = self._get_directories_from_database(result)
        for directory in directories - directories._filter_access("read"):
            file_ids -= set(directory.with_user(SUPERUSER_ID).mapped("file_ids").ids)
        return len(file_ids) if count else list(file_ids)

    def _filter_access(self, operation):
        records = super(File, self)._filter_access(operation)
        if self.env.user.id == SUPERUSER_ID:
            return records
        directories = self._get_directories_from_database(records.ids)
        for directory in directories - directories._filter_access("read"):
            records -= self.browse(
                directory.with_user(SUPERUSER_ID).mapped("file_ids").ids
            )
        return records

    def check_access(self, operation, raise_exception=False):
        res = super(File, self).check_access(operation, raise_exception)
        try:
            if self.env.user.has_group("base.group_portal"):
                res_access = res and self.check_directory_access(operation)
                return res_access and (
                    self.directory_id.id
                    not in self.directory_id._get_ids_without_access_groups(operation)
                )
            else:
                return res and self.check_directory_access(operation)
        except AccessError:
            if raise_exception:
                raise
            return False

    def check_directory_access(self, operation, vals=False, raise_exception=False):
        if not vals:
            vals = {}
        if self.env.user.id == SUPERUSER_ID:
            return True
        if "directory_id" in vals and vals["directory_id"]:
            records = self.env["dms.directory"].browse(vals["directory_id"])
        else:
            records = self._get_directories_from_database(self.ids)
        return records.check_access(operation, raise_exception)

    # ----------------------------------------------------------
    # Constrains
    # ----------------------------------------------------------

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

    @api.constrains("directory_id")
    def _check_directory_access(self):
        for record in self:
            if not record.directory_id.check_access("create", raise_exception=False):
                raise ValidationError(
                    _("The directory has to have the permission to create files.")
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
        self.check_directory_access("create", default, True)
        return super(File, self).copy(default)

    def write(self, vals):
        self.check_directory_access("write", vals, True)
        self.check_lock()
        return super(File, self).write(vals)

    def unlink(self):
        self.check_access_rights("unlink")
        self.check_directory_access("unlink", {}, True)
        self.check_lock()
        # We need to do sudo because we don't know when the related groups
        # will be deleted
        return super(File, self.sudo()).unlink()

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

    @api.model
    def _check_lock_editor(self, lock_uid):
        return lock_uid in (self.env.uid, SUPERUSER_ID)

    def check_lock(self):
        for record in self:
            if record.locked_by.exists() and not self._check_lock_editor(
                record.locked_by.id
            ):
                message = _("The record (%s [%s]) is locked, by an other user.")
                raise AccessError(message % (record._description, record.id))

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
