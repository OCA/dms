# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


def convert_root_storage_id_in_storage_id(env):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE dms_directory
        SET storage_id = root_storage_id
        WHERE root_storage_id IS NOT NULL
        AND parent_id IS NULL
        """,
    )


@openupgrade.migrate()
def migrate(env, version):
    convert_root_storage_id_in_storage_id(env)
