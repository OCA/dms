# Copyright 2020 Creu Blanca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.osv import expression


class DmsDirectory(models.Model):
    _inherit = "dms.directory"

    parent_id = fields.Many2one(default=lambda self: self._default_parent())

    @api.model
    def _default_parent(self):
        return self.env.context.get("default_parent_directory_id", False)

    @api.constrains("res_id", "is_root_directory", "storage_id", "res_model")
    def _check_resource(self):
        for directory in self:
            if directory.storage_id.save_type == "attachment":
                continue
            if (
                directory.is_root_directory
                and directory.storage_id.model_ids
                and not directory.res_id
            ):
                raise ValidationError(
                    _("Directories of this storage must be related to a record")
                )
            if not directory.res_id:
                continue
            if self.search(
                [
                    ("storage_id", "=", directory.storage_id.id),
                    ("id", "!=", directory.id),
                    ("res_id", "=", directory.res_id),
                    ("res_model", "=", directory.res_model),
                ],
                limit=1,
            ):
                raise ValidationError(
                    _("This record is already related in this storage")
                )

    @api.model
    def _build_documents_view_directory(self, directory):
        return {
            "id": f"directory_{directory.id}",
            "text": directory.name,
            "icon": "fa fa-folder-o",
            "type": "directory",
            "data": {"odoo_id": directory.id, "odoo_model": "dms.directory"},
            "children": directory.count_elements > 0,
        }

    @api.model
    def _check_parent_field(self):
        if self._parent_name not in self._fields:
            raise TypeError(f"The parent ({self._parent_name}) field does not exist.")

    @api.model
    def search_read_parents(
        self, domain=False, fields=None, offset=0, limit=None, order=None
    ):
        """This method finds the top level elements of the hierarchy
        for a given search query.

        :param domain: a search domain <reference/orm/domains> (default: empty list)
        :param fields: a list of fields to read (default: all fields of the model)
        :param offset: the number of results to ignore (default: none)
        :param limit: maximum number of records to return (default: all)
        :param order: a string to define the sort order of the query
             (default: none)
        :returns: the top level elements for the given search query
        """
        if not domain:
            domain = []
        records = self.search_parents(
            domain=domain, offset=offset, limit=limit, order=order
        )
        if not records:
            return []
        if fields and fields == ["id"]:
            return [{"id": record.id} for record in records]
        result = records.read(fields)
        if len(result) <= 1:
            return result
        index = {vals["id"]: vals for vals in result}
        return [index[record.id] for record in records if record.id in index]

    @api.model
    def search_parents(
        self, domain=False, offset=0, limit=None, order=None, count=False
    ):
        """This method finds the top level elements of the
        hierarchy for a given search query.

        :param domain: a search domain <reference/orm/domains> (default: empty list)
        :param offset: the number of results to ignore (default: none)
        :param limit: maximum number of records to return (default: all)
        :param order: a string to define the sort order of the query
             (default: none)
        :param count: counts and returns the number of matching records
             (default: False)
        :returns: the top level elements for the given search query
        """
        if not domain:
            domain = []
        res = self._search_parents(
            domain=domain, offset=offset, limit=limit, order=order, count=count
        )
        return res if count else self.browse(res)

    @api.model
    def _search_parents(
        self, domain=False, offset=0, limit=None, order=None, count=False
    ):
        if not domain:
            domain = []
        self._check_parent_field()
        self.check_access("read")
        if expression.is_false(self, domain):
            return []
        query = self._where_calc(domain)
        self._apply_ir_rules(query, "read")
        from_clause, from_params = query.from_clause
        where_clause, where_clause_arguments = query.where_clause
        parent_where = where_clause and (f" WHERE {where_clause}") or ""
        parent_query = f'SELECT "{self._table}".id FROM ' + from_clause + parent_where
        no_parent_clause = f'"{self._table}"."{self._parent_name}" IS NULL'
        no_access_clause = (
            f'"{self._table}"."{self._parent_name}" NOT IN ({parent_query})'
        )
        parent_clause = f"({no_parent_clause} OR {no_access_clause})"
        order_by = f" ORDER BY {self._order_to_sql(order, self._where_calc([])).code}"
        where_clause_params = where_clause_arguments
        where_str = (
            where_clause
            and (f" WHERE {where_clause} AND {parent_clause}")
            or (f" WHERE {parent_clause}")
        )
        if count:
            # pylint: disable=sql-injection
            query_str = "SELECT count(1) FROM " + from_clause + where_str
            self._cr.execute(query_str, where_clause_params)
            return self._cr.fetchone()[0]
        limit_str = limit and " limit %s" or ""
        offset_str = offset and " offset %s" or ""
        query_str = (
            f'SELECT "{self._table}".id FROM '
            + from_clause
            + where_str
            + order_by
            + limit_str
            + offset_str
        )
        complete_where_clause_params = where_clause_params + where_clause_arguments
        if limit:
            complete_where_clause_params.append(limit)
        if offset:
            complete_where_clause_params.append(offset)
        # pylint: disable=sql-injection
        self._cr.execute(query_str, complete_where_clause_params)
        return list({x[0] for x in self._cr.fetchall()})
