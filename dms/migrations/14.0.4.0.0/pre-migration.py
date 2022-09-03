# Copyright 2021 Tecnativa - Jairo Llopis
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from openupgradelib import openupgrade

# User-provided thumbnails that were attachment=False
column_renames = {
    "dms_file": [("custom_thumbnail", None)],
    "dms_directory": [("custom_thumbnail", None)],
}


@openupgrade.migrate()
def migrate(env, version):
    if openupgrade.column_exists(env.cr, "dms_file", "custom_thumbnail"):
        openupgrade.rename_columns(env.cr, column_renames)
