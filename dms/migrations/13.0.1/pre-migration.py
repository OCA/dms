# Copyright 2020 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade  # pylint: disable=W7936

_model_renames = [
    ("muk_dms.file", "dms.file"),
    ("muk_dms.category", "dms.category"),
    ("muk_dms.tag", "dms.tag"),
    ("muk_dms.directory", "dms.directory"),
    ("muk_dms.storage", "dms.storage"),
    ("muk_dms.mixins.thumbnail", "dms.mixins.thumbnail"),
    ("muk_security.access_groups", "dms.access.group"),
]

_table_renames = [
    ("muk_dms_file", "dms_file"),
    ("muk_dms_category", "dms_category"),
    ("muk_dms_tag", "dms_tag"),
    ("muk_dms_directory", "dms_directory"),
    ("muk_dms_storage", "dms_storage"),
    ("muk_dms_file_tag_rel", "dms_file_tag_rel"),
    ("muk_dms_directory_tag_rel", "dms_directory_tag_rel"),
    ("muk_dms_directory_star_rel", "dms_directory_star_rel"),
    ("muk_security_access_groups", "dms_access_group"),
    ("muk_security_groups_explicit_users_rel", "dms_access_group_explicit_users_rel"),
    # Security Mixin relation tables
    ("muk_dms_directory_groups_rel", "dms_directory_groups_rel"),
    ("muk_dms_directory_complete_groups_rel", "dms_directory_complete_groups_rel"),
]

_field_renames = [
    ("dms.category", "dms_category", "parent_category", "parent_id"),
    ("dms.category", "dms_category", "child_categories", "child_category_ids"),
    ("dms.category", "dms_category", "tags", "tag_ids"),
    ("dms.category", "dms_category", "directories", "directory_ids"),
    ("dms.category", "dms_category", "files", "file_ids"),
    ("dms.directory", "dms_directory", "root_storage", "root_storage_id"),
    ("dms.directory", "dms_directory", "storage", "storage_id"),
    ("dms.directory", "dms_directory", "parent_directory", "parent_id"),
    ("dms.directory", "dms_directory", "company", "company_id"),
    ("dms.directory", "dms_directory", "category", "category_id"),
    ("dms.directory", "dms_directory", "child_directories", "child_directory_ids"),
    ("dms.directory", "dms_directory", "tags", "tag_ids"),
    ("dms.directory", "dms_directory", "user_stars", "user_star_ids"),
    ("dms.directory", "dms_directory", "files", "file_ids"),
    ("dms.directory", "dms_directory", "groups", "group_ids"),
    ("dms.directory", "dms_directory", "complete_groups", "complete_group_ids"),
    ("dms.tag", "dms_tag", "category", "category_id"),
    ("dms.file", "dms_file", "directory", "directory_id"),
    ("dms.file", "dms_file", "storage", "storage_id"),
    ("dms.file", "dms_file", "company", "company_id"),
    ("dms.file", "dms_file", "category", "category_id"),
    ("dms.file", "dms_file", "tags", "tag_ids"),
    ("dms.file", "dms_file", "groups", "group_ids"),
    ("dms.file", "dms_file", "complete_groups", "complete_group_ids"),
    ("dms.file", "dms_file", "mimetype", "res_mimetype"),
    ("dms.storage", "dms_storage", "root_directories", "root_directory_ids"),
    ("dms.storage", "dms_storage", "storage_directories", "storage_directory_ids"),
    ("dms.storage", "dms_storage", "company", "company_id"),
    ("dms.storage", "dms_storage", "storage_files", "storage_file_ids"),
    ("dms.access.group", "dms_access_group", "directories", "directory_ids"),
    ("dms.access.group", "dms_access_group", "parent_group", "parent_group_id"),
    ("dms.access.group", "dms_access_group", "child_groups", "child_group_ids"),
    ("dms.access.group", "dms_access_group", "groups", "group_ids"),
    ("dms.access.group", "dms_access_group", "explicit_users", "explicit_user_ids"),
    ("dms.access.group", "dms_access_group", "users", "user_ids"),
]

# Complete name must be added manually due to its usage as order
_field_add = [("complete_name", "dms.directory", "dms_directory", "char", False, "dms")]

_config_parameters = {
    "muk_dms.forbidden_extensions": "dms.forbidden_extensions",
    "muk_web_utils.binary_max_size": "dms.binary_max_size",
}


@openupgrade.migrate()
def migrate(env, version):
    cr = env.cr
    if openupgrade.table_exists(cr, "muk_dms_file"):
        openupgrade.rename_models(cr, _model_renames)
        for table in _table_renames:
            if openupgrade.table_exists(cr, table[0]):
                openupgrade.rename_tables(cr, [table])
        for field in _field_renames:
            if openupgrade.table_exists(cr, field[1]) and openupgrade.column_exists(
                cr, field[1], field[2]
            ):
                openupgrade.rename_fields(env, [field])
        if not openupgrade.table_exists(cr, "dms_storage"):
            openupgrade.rename_models(cr, [("muk_dms.settings", "dms.storage")])
            openupgrade.rename_tables(cr, [("muk_dms_settings", "dms_storage")])
            openupgrade.rename_fields(
                env, [("dms.directory", "dms_directory", "settings", "root_storage_id")]
            )
        openupgrade.add_fields(env, _field_add)
        for key in _config_parameters:
            env["ir.config_parameter"].search([("key", "=", key)]).write(
                {"key": _config_parameters[key]}
            )
