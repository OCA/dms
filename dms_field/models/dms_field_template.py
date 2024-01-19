# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class DmsFieldTemplate(models.Model):
    _name = "dms.field.template"
    _description = "Dms Field Template"

    name = fields.Char(required=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        store=True,
        index=True,
    )
    storage_id = fields.Many2one(
        comodel_name="dms.storage",
        domain=[("save_type", "!=", "attachment")],
        string="Storage",
    )
    model_id = fields.Many2one(
        comodel_name="ir.model",
        string="Model",
        domain=[("transient", "=", False), ("model", "!=", "dms.field.template")],
        index=True,
    )
    model = fields.Char(
        compute="_compute_model", compute_sudo=True, store=True, string="Model name"
    )
    group_ids = fields.Many2many(
        comodel_name="dms.access.group",
        string="Groups",
    )
    user_field_id = fields.Many2one(
        comodel_name="ir.model.fields",
        domain="[('model_id', '=', model_id),('relation', '=', 'res.users')]",
        string="User field",
    )
    directory_format_name = fields.Char(
        string="Directory format name",
        default="{{object.display_name}}",
        help="""You can set expressions to be used for the directory name,
        e.g.: {{object.name}}""",
    )

    @api.depends("model_id")
    def _compute_model(self):
        for item in self:
            item.model = item.model_id.model

    def _get_template_from_model(self, model):
        return self.search([("model", "=", model)], limit=1)

    @api.model
    def create_dms_directory(self):
        """According to the model, create the directory linked to that record
        and the subdirectories."""
        res_model = self.env.context.get("res_model")
        res_id = self.env.context.get("res_id")
        record = self.env[res_model].browse(res_id)
        directory_model = self.env["dms.directory"].sudo()
        if res_model == "dms.field.template":
            return directory_model.create(
                {
                    "storage_id": record.storage_id.id,
                    "res_id": record.id,
                    "res_model": record._name,
                    "is_root_directory": True,
                    "name": record.display_name,
                    "group_ids": record.group_ids.ids,
                }
            )
        template = self._get_template_from_model(res_model)
        if not template:
            raise ValidationError(_("There is no template linked to this model"))
        total_directories = directory_model.search_count(
            [
                ("is_root_directory", "=", True),
                ("res_model", "=", res_model),
                ("res_id", "=", res_id),
            ]
        )
        if total_directories > 0:
            raise ValidationError(_("There is already a linked directory created."))
        # Create root directory + files
        dms_directory_ids = template.dms_directory_ids
        directory = directory_model.create(
            template._prepare_directory_vals(dms_directory_ids, record)
        )
        self._copy_files_from_directory(dms_directory_ids, directory)
        # Create child directories
        self._create_child_directories(directory, dms_directory_ids)
        return directory

    def _copy_files_from_directory(self, directory, new_directory):
        for file in directory.file_ids:
            file.copy({"directory_id": new_directory.id})

    def _set_groups_from_directory(self, directory, record):
        groups = self.env["dms.access.group"]
        for group in directory.group_ids:
            group_name = _("Autogenerate group from %(model)s (%(name)s)") % {
                "model": record._description,
                "name": record.display_name,
            }
            new_group = group.copy({"name": group_name, "directory_ids": False})
            # Apply sudo() because the user may not have permissions to access
            # ir.model.fields.
            user_field = self.sudo().user_field_id
            if user_field:
                user = record[user_field.name]
                if user:
                    new_group.write({"explicit_user_ids": [(4, user.id)]})
            groups += new_group
        return groups

    def _create_child_directories(self, parent, directory):
        # Create child directories (all leves) + files
        directory_model = self.env["dms.directory"].sudo()
        for child_directory in directory.child_directory_ids:
            child = directory_model.create(
                {
                    "name": child_directory.name,
                    "is_root_directory": False,
                    "parent_id": parent.id,
                }
            )
            self._copy_files_from_directory(child_directory, child)
            self._create_child_directories(child, child_directory)

    def _prepare_directory_vals(self, directory, record):
        groups = self._set_groups_from_directory(directory, record)
        directory_name = self.env["mail.render.mixin"]._render_template(
            self.directory_format_name,
            record._name,
            record.ids,
            engine="inline_template",
        )[record.id]
        return {
            "storage_id": directory.storage_id.id,
            "res_id": record.id,
            "res_model": record._name,
            "is_root_directory": directory.is_root_directory,
            "name": directory_name,
            "group_ids": [(4, group.id) for group in groups],
        }
