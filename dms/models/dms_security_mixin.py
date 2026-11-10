# Copyright 2020 Creu Blanca
# Copyright 2021-2025 Tecnativa - Víctor Martínez
# Copyright 2024 Subteno - Timothée Vannier (https://www.subteno.com).
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from logging import getLogger

from odoo import api, fields, models
from odoo.exceptions import AccessError
from odoo.fields import Domain
from odoo.tools import SQL

_logger = getLogger(__name__)


class DmsSecurityMixin(models.AbstractModel):
    _name = "dms.security.mixin"
    _description = "DMS Security Mixin"

    # Submodels must define this field that points to the owner dms.directory
    _directory_field = "directory_id"

    res_model = fields.Char(
        string="Linked attachments model", index="btree", store=True
    )
    res_id = fields.Integer(
        string="Linked attachments record ID", index="btree", store=True
    )
    record_ref = fields.Reference(
        string="Record Referenced",
        compute="_compute_record_ref",
        selection=lambda self: self._get_ref_selection(),
    )
    # These fields are used in ir.access domains. The ORM evaluates those domains
    # in sudo, so the values must not depend on `su` but only on the acting user.
    permission_read = fields.Boolean(
        compute="_compute_permissions",
        search="_search_permission_read",
        string="Read Access",
        compute_sudo=True,
        depends_context=("uid",),
    )
    permission_create = fields.Boolean(
        compute="_compute_permissions",
        search="_search_permission_create",
        string="Create Access",
        compute_sudo=True,
        depends_context=("uid",),
    )
    permission_write = fields.Boolean(
        compute="_compute_permissions",
        search="_search_permission_write",
        string="Write Access",
        compute_sudo=True,
        depends_context=("uid",),
    )
    permission_unlink = fields.Boolean(
        compute="_compute_permissions",
        search="_search_permission_unlink",
        string="Delete Access",
        compute_sudo=True,
        depends_context=("uid",),
    )

    @api.model
    def _get_ref_selection(self):
        # All registered models are an intentional choice here.
        # pylint: disable=no-search-all
        models = self.env["ir.model"].sudo().search([])
        return [(model.model, model.name) for model in models]

    @api.depends("res_model", "res_id")
    def _compute_record_ref(self):
        for record in self:
            record.record_ref = False
            if record.res_model and record.res_id:
                record.record_ref = f"{record.res_model},{record.res_id}"

    def _compute_permissions(self):
        """Get the permissions of the acting user on each record.

        This runs in sudo (``compute_sudo``) because the ORM reads these fields
        in sudo when it evaluates the ir.access domains. The access domain is
        therefore built for the acting user (``sudo(False)``) and searched in sudo.
        """
        operations = ("create", "read", "unlink", "write")
        user_self = self.sudo(False)
        if user_self.env.su:
            for operation in operations:
                self[f"permission_{operation}"] = True
            return
        origins = self._origin
        for operation in operations:
            domain = user_self._access_domain(operation)
            if domain.is_false() or not origins:
                allowed_ids = set()
            elif domain.is_true():
                allowed_ids = set(origins._ids)
            else:
                allowed_ids = set(
                    origins.sudo()
                    .with_context(active_test=False)
                    .search(Domain("id", "in", origins.ids) & domain)
                    ._ids
                )
            for record in self:
                origin_id = record._origin.id
                # Records not saved yet are not restricted
                record[f"permission_{operation}"] = (
                    not origin_id or origin_id in allowed_ids
                )

    @api.model
    def _invalidate_dms_permissions(self):
        """Drop the cached permissions of DMS records.

        Permissions depend on DMS access groups, directory hierarchy, storages
        and related records, which are not field dependencies.
        """
        fnames = [
            "permission_create",
            "permission_read",
            "permission_unlink",
            "permission_write",
        ]
        for model_name in ("dms.directory", "dms.file"):
            # This also invalidates the read access cache of the model
            self.env[model_name].invalidate_model(fnames)

    @api.model
    def _get_domain_by_inheritance(self, operation):
        """Get domain for inherited accessible records."""
        if self.env.su:
            return []
        inherited_access_field = "storage_id_inherit_access_from_parent_record"
        if self._name != "dms.directory":
            inherited_access_field = f"{self._directory_field}.{inherited_access_field}"
        inherited_access_domain = [
            ("storage_id_save_type", "=", "attachment"),
            (inherited_access_field, "=", True),
        ]
        domains = []
        # Get all used related records
        related_groups = self.sudo()._read_group(
            domain=inherited_access_domain + [("res_model", "!=", False)],
            groupby=["res_model"],
            aggregates=["res_id:array_agg"],
        )
        for res_model, res_id_array in related_groups:
            try:
                model = self.env[res_model]
            except KeyError:
                # The model might not be registered.
                # This is normal if you are upgrading the database.
                # Otherwise, you probably have garbage DMS data.
                # These records will be accessible by DB users only.
                domains.append(
                    [
                        ("res_model", "=", res_model),
                        (True, "=", self.env.user.has_group("base.group_user")),
                    ]
                )
                continue
            # Check model access only once per batch
            try:
                model.check_access(operation)
            except AccessError:
                continue
            domains.append([("res_model", "=", model._name), ("res_id", "=", False)])
            # Check record access in batch too
            res_ids = [i for i in res_id_array if i]  # Hack to remove None res_id
            # Apply exists to skip records that do not exist. (e.g. a res.partner
            # deleted by database).
            model_records = model.browse(res_ids).exists()
            related_ok = model_records._filtered_access(operation)
            if not related_ok:
                continue
            domains.append(
                [("res_model", "=", model._name), ("res_id", "in", related_ok.ids)]
            )
        return Domain.AND([Domain(inherited_access_domain), Domain.OR(domains)])

    @api.model
    def _get_access_groups_query(self, operation):
        """Return the query to select access groups."""
        operation_check = {
            "create": "AND dag.perm_inclusive_create",
            "read": "",
            "unlink": "AND dag.perm_inclusive_unlink",
            "write": "AND dag.perm_inclusive_write",
        }[operation]
        select = f"""(
            SELECT
                dir_group_rel.aid
            FROM
                dms_directory_complete_groups_rel AS dir_group_rel
                INNER JOIN dms_access_group AS dag
                    ON dir_group_rel.gid = dag.id
                INNER JOIN dms_access_group_users_rel AS users
                    ON users.gid = dag.id
            WHERE
                users.uid = %s {operation_check}
            )"""
        sql = SQL(
            select,
            self.env.uid,
        )
        return sql

    @api.model
    def _get_domain_by_access_groups(self, operation):
        """Get domain for records accessible applying DMS access groups."""
        result = [
            (
                f"{self._directory_field}.storage_id_inherit_access_from_parent_record",
                "=",
                False,
            ),
            (
                self._directory_field,
                "in",
                self._get_access_groups_query(operation),
            ),
        ]
        return result

    @api.model
    def _get_permission_domain(self, operator, value, operation):
        """Abstract logic for searching computed permission fields."""
        # The domain optimizer normalizes any value searched on these Boolean
        # fields to [True], flipping the operator when needed, so the operator
        # alone carries the polarity and `value` never reaches this method
        # unnormalized. ir.access domains are evaluated with su while env.uid
        # stays the acting user; sudo(False) recovers that user, except for
        # the real superuser, whose environment keeps su set.
        _self = self.sudo(False) if self.env.su else self
        positive = operator == "in"
        if _self.env.su:
            return Domain.TRUE if positive else Domain.FALSE
        result = Domain.OR(
            [
                _self._get_domain_by_access_groups(operation),
                _self._get_domain_by_inheritance(operation),
            ]
        )
        # `determine_domain` dispatches negative operators straight to this
        # search method, so `not in` must be negated here.
        return result if positive else ~result

    @api.model
    def _search_permission_create(self, operator, value):
        return self._get_permission_domain(operator, value, "create")

    @api.model
    def _search_permission_read(self, operator, value):
        return self._get_permission_domain(operator, value, "read")

    @api.model
    def _search_permission_unlink(self, operator, value):
        return self._get_permission_domain(operator, value, "unlink")

    @api.model
    def _search_permission_write(self, operator, value):
        return self._get_permission_domain(operator, value, "write")

    def _can_return_content(self, field_name=None, access_token=None):
        # Used to display the icon/preview in the portal: the user might not
        # have access to the record, but the token makes it public.
        if access_token and self.sudo().check_access_token(access_token):
            return True
        return super()._can_return_content(field_name, access_token)

    def _check_access_dms_record(self, operation: str) -> None:
        """Raise an AccessError if the acting user can't perform ``operation``
        on all the records, according to the ir.access permissions and
        restrictions (DMS computed permissions included)."""
        if not any(self._ids) or self.env.su:
            return
        domain = self._access_domain(operation)
        allowed = self.browse()
        if not domain.is_false():
            allowed = (
                self.sudo()
                .with_context(active_test=False)
                .search(Domain("id", "in", self.ids) & domain)
                .with_env(self.env)
            )
        forbidden = self - allowed
        if forbidden:
            raise forbidden._make_access_error_message(operation, domain)

    @api.model_create_multi
    def create(self, vals_list):
        # Create as sudo to avoid testing creation permissions before DMS security
        # groups are attached (otherwise nobody would be able to create)
        res = super(DmsSecurityMixin, self.sudo()).create(vals_list)
        # Need to flush now, so all groups are stored in DB and the SELECT used
        # to check access works
        res.flush_recordset()
        self._invalidate_dms_permissions()
        # Go back to the original sudo state and check we really had creation permission
        res = res.sudo(self.env.su)
        res._check_access_dms_record("create")
        return res

    def write(self, vals):
        # The standard check_access() is also done by the ORM, but it relies on
        # cached permissions that we want fresh here.
        self._check_access_dms_record("write")
        res = super().write(vals)
        self._invalidate_dms_permissions()
        return res

    def unlink(self):
        self._check_access_dms_record("unlink")
        res = super().unlink()
        self._invalidate_dms_permissions()
        return res
