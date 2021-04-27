# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade  # pylint: disable=W7936

_field_renames = [
    ("dms.file", "dms_file", "res_mimetype", "mimetype"),
]


@openupgrade.migrate()
def migrate(env, version):
    cr = env.cr
    for field in _field_renames:
        if openupgrade.table_exists(cr, field[1]) and openupgrade.column_exists(
            cr, field[1], field[2]
        ):
            openupgrade.rename_fields(env, [field])
