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
    permission_read = fields.Boolean(
        compute="_compute_permissions",
        search="_search_permission_read",
        string="Read Access",
    )
    permission_create = fields.Boolean(
        compute="_compute_permissions",
        search="_search_permission_create",
        string="Create Access",
    )
    permission_write = fields.Boolean(
        compute="_compute_permissions",
        search="_search_permission_write",
        string="Write Access",
    )
    permission_unlink = fields.Boolean(
        compute="_compute_permissions",
        search="_search_permission_unlink",
        string="Delete Access",
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
        """
        Get permissions for the current record.
        """

        # Update according to presence when applying ir.rule
        self.invalidate_recordset()
        if self.env.su:
            self.update(
                {
                    "permission_create": True,
                    "permission_read": True,
                    "permission_unlink": True,
                    "permission_write": True,
                }
            )
            return

        creatable = self._filtered_access("create")
        readable = self._filtered_access("read")
        unlinkable = self._filtered_access("unlink")
        writeable = self._filtered_access("write")
        for one in self:
            one.update(
                {
                    "permission_create": bool(one & creatable),
                    "permission_read": bool(one & readable),
                    "permission_unlink": bool(one & unlinkable),
                    "permission_write": bool(one & writeable),
                }
            )

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
        _self = self
        # HACK ir.rule domain is always computed with sudo, so if this check is
        # true, we can assume safely that you're checking permissions
        if self.env.su and value == self.env.uid:
            _self = self.sudo(False)
            value = bool(value)
        # Tricky one, to know if you want to search
        # positive or negative access
        positive = (operator not in Domain.NEGATIVE_OPERATORS) == bool(value)
        if _self.env.su:
            # You're SUPERUSER_ID
            return Domain.TRUE if positive else Domain.FALSE

        result = Domain.OR(
            [
                _self._get_domain_by_access_groups(operation),
                _self._get_domain_by_inheritance(operation),
            ]
        )
        if not positive:
            # Domain is immutable in 19.0; use the bitwise invert operator
            # (replaces the 18.0 ``result.insert(0, "!")`` mutation).
            result = ~Domain(result)
        return result

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

    def filtered_domain(self, domain):
        """This method is needed to inhibit the behavior when called from the
        _check_access() method with sudo() https://github.com/odoo/odoo/blob/fc737a147b9aefbd6ae5d111835ce3f4f7b4240a/odoo/models.py#L4465.
        It would cause the error that multiple records are not accessed to be
        displayed.
        The _filtered_access() method is also overwritten to prevent this sudo()
        specific behavior and to be able to access only the appropriate records.
        """
        if self.env.su:
            return self
        return super().filtered_domain(domain)

    def _filtered_access_no_recursion(self, operation: str):
        """This method is just the same as _filtered_access
        but it can not be called withoud super due to
        recursion error.
        """
        if self and not self.env.su and (result := self._check_access(operation)):
            return self - result[0]
        return self

    def _filtered_access(self, operation):
        # Only kept to not break inheritance; see next comment
        result = super()._filtered_access(operation)
        # HACK Always fall back to applying rules by SQL.
        # Upstream `_filtered_access()` doesn't use computed fields
        # search methods. Thus, it will take the `[('permission_{operation}',
        # '=', user.id)]` rule literally. Obviously that will always fail
        # because `self[f"permission_{operation}"]` will always be a `bool`,
        # while `user.id` will always be an `int`.
        result |= self._filtered_access_no_recursion(operation)
        return result

    def _check_access_dms_record(self, operation: str) -> tuple | None:
        """Specific method "similar" to _check_access() but with a different
        behavior: check if you do not really have access to any of the records
        in to avoid performing the corresponding create/write/unlink action."""
        if any(self._ids) and not self.env.su:
            Rule = self.env["ir.rule"]
            domain = Rule._compute_domain(self._name, operation)
            items = self.with_context(active_test=False).search(domain)
            if any(x_id not in items.ids for x_id in self.ids):
                raise Rule._make_access_error(operation, (self - items))

    @api.model
    def _search(self, domain, *args, **kwargs):
        """Inject the DMS access-group + inheritance filter into reads.

        ``ir.rule._compute_domain()`` runs the basic Domain optimizer
        (``Domain.optimize``, not ``Domain.optimize_full``), so ``search=``
        methods on non-stored computed fields like ``permission_read`` are
        silently bypassed when ``domain_force`` is evaluated. The read-side
        ``ir.rule`` records on ``dms.directory`` / ``dms.file`` would
        therefore no-op and every user would see every record. We restore
        the intended behaviour by AND-ing the same domain directly into the
        search here, where SQL translation runs the full optimizer that
        does honour ``search=`` methods.

        Notes:
        - ``env.su`` short-circuits the filter (superuser sees everything).
        - The context flag ``dms_skip_access_filter`` lets internal helpers
          (``_get_domain_by_inheritance``'s ``_read_group`` etc.) bypass the
          filter on their recursive reads, avoiding O(N) blow-up.
        - The filter targets the ``read`` operation. Write/create/unlink
          validation continues via ``_check_access_dms_record`` (called from
          ``create``/``write``/``unlink`` in this mixin) plus the
          ``_search_permission_*`` methods for explicit
          ``('permission_<op>', '=', user.id)`` clauses in caller domains.
        """
        if not self.env.su and not self.env.context.get("dms_skip_access_filter"):
            self = self.with_context(dms_skip_access_filter=True)
            dms_domain = Domain.OR(
                [
                    self._get_domain_by_access_groups("read"),
                    self._get_domain_by_inheritance("read"),
                ]
            )
            domain = Domain.AND([Domain(domain), dms_domain])
        return super()._search(domain, *args, **kwargs)

    @api.model_create_multi
    def create(self, vals_list):
        # Create as sudo to avoid testing creation permissions before DMS security
        # groups are attached (otherwise nobody would be able to create)
        res = super(DmsSecurityMixin, self.sudo()).create(vals_list)
        # Need to flush now, so all groups are stored in DB and the SELECT used
        # to check access works
        res.flush_recordset()
        # Go back to the original sudo state and check we really had creation permission
        res = res.sudo(self.env.su)
        res._check_access_dms_record("create")
        return res

    def write(self, vals):
        self._check_access_dms_record("write")
        return super().write(vals)

    def unlink(self):
        self._check_access_dms_record("unlink")
        return super().unlink()
