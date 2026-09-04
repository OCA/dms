# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    """If there were archived users linked in `explicit_user_ids`, the relationship
    did exist in the `dms_access_group_explicit_users_rel` table; therefore, those
    users will now "appear" in `explicit_user_ids`, and it will be necessary to call
    the `_compute_users()` method so that the `users` and `count_users` fields have
    the correct values.
    It is extremely important that the `users` field has the correct values; otherwise,
    if we activate any of those users, they will not be able to view the linked records.
    We set `active_test=False` in the search context to ensure that archived users are
    taken into account, even though the `explicit_user_ids` field has that context
    defined in the field itself.
    """
    groups = (
        env["dms.access.group"]
        .sudo()
        .with_context(active_test=False)
        .search([("explicit_user_ids.active", "=", False)])
    )
    if groups:
        groups._compute_users()
