# Copyright 2020 Antoni Romera
# Copyright 2017-2019 MuK IT GmbH
# Copyright 2021 Tecnativa - Víctor Martínez
# Copyright 2024 Subteno - Timothée Vannier (https://www.subteno.com).
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64
import hashlib
import json
import logging
from collections import defaultdict

from PIL import Image

from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools import consteq, human_size
from odoo.tools.mimetypes import guess_mimetype

from ..tools import file

_logger = logging.getLogger(__name__)


class DMSFile(models.Model):
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

    # Database
    active = fields.Boolean(
        string="Archived",
        default=True,
        help="If a file is set to archived, it is not displayed, but still exists.",
    )
    directory_id = fields.Many2one(
        comodel_name="dms.directory",
        string="Directory",
        domain="[('permission_create', '=', True)]",
        context={"dms_directory_show_path": True},
        ondelete="restrict",
        auto_join=True,
        required=True,
        index="btree",
        tracking=True,  # Leave log if "moved" to another directory
    )
    root_directory_id = fields.Many2one(related="directory_id.root_directory_id")
    # Override acording to defined in AbstractDmsMixin
    storage_id = fields.Many2one(
        related="directory_id.storage_id",
        readonly=True,
        prefetch=False,
    )

    path_names = fields.Char(
        compute="_compute_path",
        compute_sudo=True,
        readonly=True,
        store=False,
    )

    path_json = fields.Text(
        compute="_compute_path",
        compute_sudo=True,
        readonly=True,
        store=False,
    )

    tag_ids = fields.Many2many(
        comodel_name="dms.tag",
        relation="dms_file_tag_rel",
        column1="fid",
        column2="tid",
        domain="['|', ('category_id', '=', False),('category_id', '=?', category_id)]",
        string="Tags",
    )

    content = fields.Binary(
        compute="_compute_content",
        inverse="_inverse_content",
        attachment=False,
        prefetch=False,
        required=True,
        store=False,
    )

    extension = fields.Char(compute="_compute_extension", readonly=True, store=True)

    mimetype = fields.Char(
        compute="_compute_mimetype", string="Type", readonly=True, store=True
    )

    size = fields.Float(readonly=True)
    human_size = fields.Char(
        readonly=True,
        string="Size (human readable)",
        compute="_compute_human_size",
        store=True,
    )

    checksum = fields.Char(string="Checksum/SHA1", readonly=True, index="btree")

    content_binary = fields.Binary(attachment=False, prefetch=False)

    save_type = fields.Char(
        compute="_compute_save_type",
        string="Current Save Type",
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
    content_file = fields.Binary(attachment=True, prefetch=False)

    # Extend inherited field(s)
    image_1920 = fields.Image(compute="_compute_image_1920", store=True, readonly=False)

    @api.depends("mimetype", "content")
    def _compute_image_1920(self):
        """Provide thumbnail automatically if possible."""
        for one in self.filtered("mimetype"):
            # Image.MIME provides a dict of mimetypes supported by Pillow,
            # SVG is not present in the dict but is also a supported image format
            # lacking a better solution, it's being added manually
            # Some component modifies the PIL dictionary by adding PDF as a valid
            # image type, so it must be explicitly excluded.
            if one.mimetype != "application/pdf" and one.mimetype in (
                *Image.MIME.values(),
                "image/svg+xml",
            ):
                one.image_1920 = one.content

    def check_access_rule(self, operation):
        self.mapped("directory_id").check_access_rule(operation)
        return super().check_access_rule(operation)

    def _compute_access_url(self):
        res = super()._compute_access_url()
        for item in self:
            item.access_url = "/my/dms/file/%s/download" % (item.id)
        return res

    def check_access_token(self, access_token=False):
        if not access_token:
            return False

        if self.access_token and consteq(self.access_token, access_token):
            return True

        items = (
            self.env["dms.directory"]
            .sudo()
            .search([("access_token", "=", access_token)])
        )
        if items:
            item = items[0]
            if self.directory_id.id == item.id:
                return True
            directory_item = self.directory_id
            while directory_item.parent_id:
                if directory_item.id == self.directory_id.id:
                    return True
                directory_item = directory_item.parent_id
            # Fix last level
            if directory_item.id == self.directory_id.id:
                return True
        return False

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
        ondelete="cascade",
    )

    def get_human_size(self):
        return human_size(self.size)

    # Helper
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

    # Actions
    def action_migrate(self, should_logging=True):
        record_count = len(self)
        index = 1
        for dms_file in self:
            if should_logging:
                _logger.info(
                    _(
                        "Migrate File %(index)s of %(record_count)s [ %("
                        "dms_file_migration)s ]",
                        index=index,
                        record_count=record_count,
                        dms_file_migration=dms_file.migration,
                    )
                )
                index += 1
            dms_file.write(
                {
                    "content": dms_file.with_context(**{}).content,
                    "storage_id": dms_file.directory_id.storage_id.id,
                }
            )

    def action_save_onboarding_file_step(self):
        self.env.user.company_id.set_onboarding_step_done(
            "documents_onboarding_file_state"
        )

    def action_wizard_dms_file_move(self):
        items = self.browse(self.env.context.get("active_ids"))
        root_directories = items.mapped("root_directory_id")
        if len(root_directories) > 1:
            raise UserError(_("Only files in the same root directory can be moved."))
        result = self.env["ir.actions.act_window"]._for_xml_id(
            "dms.wizard_dms_file_move_act_window"
        )
        result["context"] = dict(self.env.context)
        return result

    # SearchPanel
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
        """This method is overwritten to make it 'similar' to v13.
        The goal is that the directory searchpanel shows all directories
        (even if some folders have no files).
        """
        if field_name != "directory_id":
            context = {}
            if field_name == "category_id":
                context["category_short_name"] = True
            return super(
                DMSFile, self.with_context(**context)
            ).search_panel_select_range(field_name, **kwargs)

        domain = [("is_hidden", "=", False)]
        # If we pass by context something, we filter more about it we filter
        # the directories of the files, or we show all of them
        if self.env.context.get("active_model") == "dms.directory":
            active_id = self.env.context.get("active_id")
            files = self.env["dms.file"].search(
                [("directory_id", "child_of", active_id)]
            )
            all_directory_ids = []
            for file_record in files:
                directory = file_record.directory_id
                while directory:
                    all_directory_ids.append(directory.id)
                    directory = directory.parent_id
            domain.append(("id", "in", all_directory_ids))
        # Get all possible directories
        comodel_records = (
            self.env["dms.directory"]
            .with_context(directory_short_name=True)
            .search_read(domain, ["display_name", "parent_id"])
        )
        all_record_ids = [rec["id"] for rec in comodel_records]
        field_range = {}
        enable_counters = kwargs.get("enable_counters")
        for record in comodel_records:
            record_id = record["id"]
            parent = record["parent_id"]
            record_values = {
                "id": record_id,
                "display_name": record["display_name"],
                # If the parent directory is not in all the records we should not
                # set parent_id because the user does not have access to parent.
                "parent_id": (
                    parent[0] if parent and parent[0] in all_record_ids else False
                ),
            }
            if enable_counters:
                record_values["__count"] = 0
            field_range[record_id] = record_values
        if enable_counters:
            res = super().search_panel_select_range(field_name, **kwargs)
            for item in res["values"]:
                if item["id"] in field_range:
                    field_range[item["id"]]["__count"] = item["__count"]
        return {"parent_field": "parent_id", "values": list(field_range.values())}

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
                DMSFile, self.with_context(directory_short_name=True)
            ).search_panel_select_multi_range(
                field_name, comodel_domain=directory_comodel_domain, **kwargs
            )
        return super(
            DMSFile, self.with_context(directory_short_name=True)
        ).search_panel_select_multi_range(field_name, **kwargs)

    # Read
    @api.depends("name", "directory_id", "directory_id.parent_path")
    def _compute_path(self):
        model = self.env["dms.directory"]
        for record in self:
            path_names = [record.display_name]
            path_json = [
                {
                    "model": record._name,
                    "name": record.display_name,
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
                        "id": current_dir._origin.id,
                    },
                )
                current_dir = current_dir.parent_id
            record.update(
                {
                    "path_names": "/".join(path_names) if all(path_names) else "",
                    "path_json": json.dumps(path_json),
                }
            )

    @api.depends("name", "mimetype", "content")
    def _compute_extension(self):
        for record in self:
            record.extension = file.guess_extension(
                record.name, record.mimetype, record.content
            )

    @api.depends("content")
    def _compute_mimetype(self):
        for record in self:
            binary = base64.b64decode(record.content or "")
            record.mimetype = guess_mimetype(binary)

    @api.depends("size")
    def _compute_human_size(self):
        for item in self:
            item.human_size = human_size(item.size)

    @api.depends("content_binary", "content_file", "attachment_id")
    def _compute_content(self):
        bin_size = self.env.context.get("bin_size", False)
        for record in self:
            if record.content_file:
                context = {"human_size": True} if bin_size else {"base64": True}
                record.content = record.with_context(**context).content_file
            elif record.content_binary:
                record.content = (
                    record.content_binary
                    if bin_size
                    else base64.b64encode(record.content_binary)
                )
            elif record.attachment_id:
                context = {"human_size": True} if bin_size else {"base64": True}
                record.content = record.with_context(**context).attachment_id.datas

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
                record.migration = f"{file_label} > {storage_label}"
                record.require_migration = True

    # View
    @api.onchange("category_id")
    def _change_category(self):
        self.tag_ids = self.tag_ids.filtered(
            lambda rec: not rec.category_id or rec.category_id == self.category_id
        )

    # Constrains
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
            files = record.sudo().directory_id.file_ids
            if files.filtered(
                lambda file, record=record: file.name == record.name and file != record
            ):
                raise ValidationError(
                    _("A file with the same name already exists in this directory.")
                )

    @api.constrains("extension")
    def _check_extension(self):
        if self.filtered(
            lambda rec: rec.extension
            and rec.extension in self._get_forbidden_extensions()
        ):
            raise ValidationError(_("The file has a forbidden file extension."))

    @api.constrains("size")
    def _check_size(self):
        if self.filtered(
            lambda rec: rec.size > self._get_binary_max_size() * 1024 * 1024
        ):
            raise ValidationError(
                _("The maximum upload size is %s MB.") % self._get_binary_max_size()
            )

    # Create, Update, Delete
    def _inverse_content(self):
        updates = defaultdict(set)
        for record in self:
            values = self._get_content_inital_vals()
            binary = base64.b64decode(record.content or "")
            values = record._update_content_vals(values, binary)
            updates[tools.frozendict(values)].add(record.id)
        for vals, ids in updates.items():
            self.browse(ids).write(dict(vals))

    def _create_model_attachment(self, vals):
        res_vals = vals.copy()
        directory_id = False
        if "directory_id" in res_vals:
            directory_id = res_vals["directory_id"]
        elif self.env.context.get("active_id"):
            directory_id = self.env.context.get("active_id")
        elif self.env.context.get("default_directory_id"):
            directory_id = self.env.context.get("default_directory_id")
        directory = self.env["dms.directory"].browse(directory_id)
        if (
            directory.res_model
            and directory.res_id
            and directory.storage_id_save_type == "attachment"
        ):
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
        names = self.sudo().directory_id.file_ids.mapped("name")
        if "directory_id" in default:
            directory = self.env["dms.directory"].browse(
                default.get("directory_id", False)
            )
            names = directory.sudo().file_ids.mapped("name")
        default.update({"name": file.unique_name(self.name, names, self.extension)})
        return super().copy(default)

    @api.model_create_multi
    def create(self, vals_list):
        new_vals_list = []
        for vals in vals_list:
            if "attachment_id" not in vals:
                vals = self._create_model_attachment(vals)
            new_vals_list.append(vals)
        return super().create(new_vals_list)

    # ----------------------------------------------------------
    # Locking fields and functions
    locked_by = fields.Many2one(comodel_name="res.users")

    is_locked = fields.Boolean(compute="_compute_locked", string="Locked")

    is_lock_editor = fields.Boolean(compute="_compute_locked", string="Editor")

    # ----------------------------------------------------------
    # Locking
    # ----------------------------------------------------------

    def lock(self):
        self.write({"locked_by": self.env.uid})

    def unlock(self):
        self.write({"locked_by": None})

    # Read, View
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

    def get_attachment_object(self, attachment):
        return {
            "name": attachment.name,
            "datas": attachment.datas,
            "res_model": attachment.res_model,
            "mimetype": attachment.mimetype,
        }

    @api.model
    def get_dms_files_from_attachments(self, attachment_ids=None):
        """Get the dms files from uploaded attachments.
        :return: An Array of dms files.
        """
        if not attachment_ids:
            raise UserError(_("No attachment was provided"))

        attachments = self.env["ir.attachment"].browse(attachment_ids)

        if any(
            attachment.res_id or attachment.res_model != "dms.file"
            for attachment in attachments
        ):
            raise UserError(_("Invalid attachments!"))

        return [self.get_attachment_object(attachment) for attachment in attachments]
