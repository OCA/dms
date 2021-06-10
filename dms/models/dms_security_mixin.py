# Copyright 2020 Creu Blanca
# Copyright 2021 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from collections import defaultdict

from psycopg2 import sql

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import AccessError


class DmsSecurityMixin(models.AbstractModel):
    _name = "dms.security.mixin"
    _description = "DMS Security Mixin"

    # If set the group fields are restricted by the access group
    _access_groups_fields = False

    # If set the group fields are recomputed as super administrator
    _access_groups_sudo = True

    # Set it to True to enforced security even if no group has been set
    _access_groups_strict = False

    permission_read = fields.Boolean(
        compute="_compute_permissions_read",
        search="_search_permission_read",
        string="Read Access",
    )

    permission_create = fields.Boolean(
        compute="_compute_permissions_create",
        search="_search_permission_create",
        string="Create Access",
    )

    permission_write = fields.Boolean(
        compute="_compute_permissions_write",
        search="_search_permission_write",
        string="Write Access",
    )

    permission_unlink = fields.Boolean(
        compute="_compute_permissions_unlink",
        search="_search_permission_unlink",
        string="Delete Access",
    )

    @api.model
    def _add_magic_fields(self):
        super(DmsSecurityMixin, self)._add_magic_fields()

        def add(name, field):
            if name not in self._fields:
                self._add_field(name, field)

        add(
            "group_ids",
            fields.Many2many(
                _module=self._module,
                comodel_name="dms.access.group",
                relation="%s_groups_rel" % (self._table),
                column1="aid",
                column2="gid",
                string="Groups",
                automatic=True,
                groups=self._access_groups_fields,
            ),
        )
        add(
            "complete_group_ids",
            fields.Many2many(
                _module=self._module,
                comodel_name="dms.access.group",
                relation="%s_complete_groups_rel" % (self._table),
                column1="aid",
                column2="gid",
                string="Complete Groups",
                compute="_compute_groups",
                readonly=True,
                store=True,
                automatic=True,
                compute_sudo=self._access_groups_sudo,
                groups=self._access_groups_fields,
            ),
        )

    def _filter_access(self, operation):
        rec = self
        if self.check_access_rights(operation, False):
            rec = self._filter_access_rules(operation)
        return rec.filter_access_groups(operation)

    def _filter_access_ids(self, operation):
        return self._filter_access(operation).ids

    @api.model
    def _apply_access_groups(self, query, mode="read"):
        if self.env.user.id == SUPERUSER_ID:
            return None
        # Fix access directory and files with share button (public)
        if self.env.user.has_group("base.group_public"):
            return None

        field = "id"
        if self._name == "dms.file":
            field = "directory_id"
        where_clause = """
            "{table}".{field} IN (
                SELECT r.aid
                FROM dms_directory_complete_groups_rel r
                JOIN dms_access_group g ON r.gid = g.id
                JOIN dms_access_group_users_rel u ON r.gid = u.gid
                WHERE u.uid = %s AND (
                    (%s = 'read' AND g.perm_read) OR
                    (%s = 'create' AND g.perm_create) OR
                    (%s = 'write' AND g.perm_write) OR
                    (%s = 'unlink' AND g.perm_unlink)
                )
            )
        """.format(
            table=self._table, field=field
        )
        if not self._access_groups_strict:
            exists_clause = """
                NOT EXISTS (
                    SELECT 1
                        FROM dms_directory_complete_groups_rel r
                        JOIN dms_access_group g ON r.gid = g.id
                        WHERE r.aid = "{table}".{field}
                )
            """
            exists_clause = exists_clause.format(table=self._table, field=field)
            where_clause = "({groups_clause} OR {exists_clause})".format(
                groups_clause=where_clause, exists_clause=exists_clause
            )
        query.where_clause += [where_clause]
        query.where_clause_params += [self.env.user.id] + ([mode] * 4)
        # Add _get_directory_ids_with_res_model_without_access
        if self.env.context.get("use_res_model_without_access", True):
            custom_ids = self._get_directory_ids_with_res_model_without_access(mode)
            if custom_ids:
                extra_clause = """
                    "{table}".{field} NOT IN ({ids})
                """.format(
                    table=self._table,
                    field=field,
                    ids=", ".join(["%s"] * len(custom_ids)),
                )
                query.where_clause += [extra_clause]
                query.where_clause_params += custom_ids.ids

    @api.model
    def _apply_ir_rules(self, query, mode="read"):
        super(DmsSecurityMixin, self)._apply_ir_rules(query, mode=mode)
        self._apply_access_groups(query, mode=mode)

    def _get_ids_without_access_groups(self, operation):
        sql_query = sql.SQL(
            """
            SELECT id
            FROM {self_table} a
            WHERE NOT EXISTS (
                SELECT 1
                FROM {rel_table} r
                JOIN dms_access_group g ON r.gid = g.id AND r.aid = a.id
                WHERE r.aid = ANY (%(subset_ids)s)
            )
            """
        )
        sql_query = sql_query.format(
            self_table=sql.Identifier(self._table),
            rel_table=sql.Identifier(self._table + "_complete_groups_rel"),
        )
        self.env.cr.execute(sql_query, {"subset_ids": self.ids})
        return list(map(lambda val: val[0], self.env.cr.fetchall()))

    @api.model
    def _search_permission_read(self, operator, operand):
        if operator == "=" and operand:
            return [("id", "in", self.search([])._filter_access_ids("read"))]
        return [("id", "not in", self.search([])._filter_access_ids("read"))]

    @api.model
    def _search_permission_create(self, operator, operand):
        if operator == "=" and operand:
            return [("id", "in", self.search([])._filter_access_ids("create"))]
        return [("id", "not in", self.search([])._filter_access_ids("create"))]

    @api.model
    def _search_permission_write(self, operator, operand):
        if operator == "=" and operand:
            return [("id", "in", self.search([])._filter_access_ids("write"))]
        return [("id", "not in", self.search([])._filter_access_ids("write"))]

    @api.model
    def _search_permission_unlink(self, operator, operand):
        if operator == "=" and operand:
            return [("id", "in", self.search([])._filter_access_ids("unlink"))]
        return [("id", "not in", self.search([])._filter_access_ids("unlink"))]

    def _compute_permissions_read(self):
        records = self._filter_access("read")
        for record in records:
            record.update({"permission_read": True})
        for record in self - records:
            record.update({"permission_read": False})

    def _compute_permissions_create(self):
        records = self._filter_access("create")
        for record in records:
            record.update({"permission_create": True})
        for record in self - records:
            record.update({"permission_create": False})

    def _compute_permissions_write(self):
        records = self._filter_access("write")
        for record in records:
            record.update({"permission_write": True})
        for record in self - records:
            record.update({"permission_write": False})

    def _compute_permissions_unlink(self):
        records = self._filter_access("unlink")
        for record in records:
            record.update({"permission_unlink": True})
        for record in self - records:
            record.update({"permission_unlink": False})

    def check_access(self, operation, raise_exception=False):
        try:
            access_right = self.check_access_rights(operation, raise_exception)
            access_rule = self.check_access_rule(operation) is None
            access_group = self.check_access_groups(operation) is None
            return access_right and access_rule and access_group
        except AccessError:
            if raise_exception:
                raise
            return False

    def check_access_groups(self, operation):
        if self.env.user.id == SUPERUSER_ID:
            return None
        group_ids = list(
            set(self.ids) - set(self._get_ids_without_access_groups(operation))
        )
        if group_ids:
            sql_query = sql.SQL(
                """
                SELECT r.aid, perm_read, perm_create, perm_write, perm_unlink
                FROM {rel_table} r
                JOIN dms_access_group g ON r.gid = g.id
                JOIN dms_access_group_users_rel u ON r.gid = u.gid
                WHERE r.aid = ANY (%(group_ids)s) AND u.uid = %(uid)s;
                """
            ).format(rel_table=sql.Identifier(self._table + "_complete_groups_rel"),)
            self.env.cr.execute(
                sql_query, {"group_ids": group_ids, "uid": self.env.user.id}
            )
            result = defaultdict(list)
            for val in self.env.cr.dictfetchall():
                result[val["aid"]].append(val["perm_%s" % operation])
            if (
                len(result.keys()) < len(group_ids)
                or not all(list(map(lambda val: any(val), result.values())))
            ) and not self.check_access(operation):
                raise AccessError(
                    _(
                        "The requested operation cannot be completed due "
                        "to group security restrictions. "
                        "Please contact your system administrator."
                        "\n\n(Document type: %s, Operation: %s)"
                    )
                    % (self._description, operation)
                )

    def filter_access_groups(self, operation):
        if self.env.user.id == SUPERUSER_ID:
            return self
        ids_with_access = self._get_ids_without_access_groups(operation)
        group_ids = list(set(self.ids) - set(ids_with_access))
        if group_ids:
            sql_query = sql.SQL(
                """
                SELECT r.aid
                FROM {rel_table} r
                JOIN dms_access_group g ON r.gid = g.id
                JOIN dms_access_group_users_rel u ON r.gid = u.gid
                WHERE
                    r.aid = ANY (%(ids)s) AND
                    u.uid = %(uid)s AND (
                        (%(operation)s = 'read' AND g.perm_read) OR
                        (%(operation)s = 'create' AND g.perm_create) OR
                        (%(operation)s = 'write' AND g.perm_write) OR
                        (%(operation)s = 'unlink' AND g.perm_unlink)
                    )
            """
            ).format(rel_table=sql.Identifier(self._table + "_complete_groups_rel"),)
            self.env.cr.execute(
                sql_query,
                {"ids": group_ids, "uid": self.env.user.id, "operation": operation},
            )
            ids_with_access += list(map(lambda val: val[0], self.env.cr.fetchall()))
        return self & self.browse(ids_with_access)

    def _get_directory_ids_with_res_model_without_access(self, operation):
        """
        It's necessary to get all directories with res_model related and check
        if access to related record.
        Context use_res_model_without_access=False is used to skip some
        part of functions that use these function and prevent recursion error.
        """
        return (
            self.env["dms.directory"]
            .with_context(use_res_model_without_access=False)
            .search(
                [
                    ("res_model", "!=", False),
                    ("storage_id_inherit_access_from_parent_record", "=", True),
                ]
            )
            .filtered(lambda x: not x.check_access("read"))
        )

    def _write(self, vals):
        self.check_access_groups("write")
        return super(DmsSecurityMixin, self)._write(vals)

    def unlink(self):
        self.check_access_groups("unlink")
        return super(DmsSecurityMixin, self).unlink()

    @api.depends("group_ids")
    def _compute_groups(self):
        for record in self:
            record.complete_group_ids = record.group_ids
