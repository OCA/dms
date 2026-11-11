# Copyright 2026 NovoAuxilia
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    """Access groups built from Odoo groups only counted the users explicitly in
    those groups, so users who get them through another group (e.g. DMS managers)
    lost access to the directories. Recompute them with the implied users.
    """
    groups = (
        env["dms.access.group"]
        .sudo()
        .with_context(active_test=False)
        .search([("group_ids", "!=", False)])
    )
    if groups:
        groups._compute_users()
