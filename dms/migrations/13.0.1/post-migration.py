# Copyright 2020 Creu Blanca
# Copyright 2020 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade  # pylint: disable=W7936


def recompute_file_content(env):
    for file in env["dms.file"].search([]):
        if "." in file.extension:
            file.extension = file.extension.replace(".", "")
        try:
            file.content
        except Exception:
            env.cr.execute("SELECT reference FROM dms_file where id = %s", (file.id,))
            result = env.cr.fetchone()
            reference_id = int(result[0].split(",")[1])
            env.cr.execute(
                "SELECT data FROM muk_dms_data_database where id = %s", (reference_id,)
            )
            content = env.cr.fetchone()
            file.content = content[0]


@openupgrade.migrate()
def migrate(env, version):
    env["dms.directory"].search([])._compute_complete_name()
    if version < "12.0.2.0.0":
        recompute_file_content(env)
