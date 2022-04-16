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
            if not directory.is_root_directory:
                raise ValidationError(
                    _("Directory %s must be root in order to be related to a " "record")
                    % directory.display_name
                )
            if not directory.storage_id.model_ids:
                raise ValidationError(
                    _(
                        "Storage %s should need to be assigned to a model in "
                        "order to relate the directory to a record"
                    )
                    % directory.storage_id.display_name
                )
            if directory.res_model not in directory.storage_id.model_ids.mapped(
                "model"
            ):
                raise ValidationError(
                    _(
                        "Storage %s should need to be assigned to "
                        "a model related to the storage"
                    )
                    % directory.storage_id.display_name
                )
            if self.search(
                [
                    ("storage_id", "=", directory.storage_id.id),
                    ("id", "!=", directory.id),
                    ("res_id", "=", directory.res_id),
                    ("res_model", "=", directory.res_model),
                    ("is_root_directory", "=", True),
                ],
                limit=1,
            ):
                raise ValidationError(
                    _("This record is already related in this storage")
                )

    @api.model
    def _build_documents_view_directory(self, directory):
        return {
            "id": "directory_%s" % directory.id,
            "text": directory.name,
            "icon": "fa fa-folder-o",
            "type": "directory",
            "data": {"odoo_id": directory.id, "odoo_model": "dms.directory"},
            "children": directory.count_elements > 0,
        }

    def _build_documents_view_initial(self):
        if len(self) == 1:
            return [self._build_documents_view_directory(self)]
        else:
            initial_data = []
            subdirectories = self.env["dms.directory"]
            for record in self.with_context(prefetch_fields=False):
                subdirectories |= (
                    record.search([("parent_id", "child_of", record.id)]) - record
                )
            for record in self - subdirectories:
                initial_data.append(record._build_documents_view_directory(record))
            return initial_data

    @api.model
    def _check_parent_field(self):
        if self._parent_name not in self._fields:
            raise TypeError("The parent (%s) field does not exist." % self._parent_name)

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
        self.check_access_rights("read")
        if expression.is_false(self, domain):
            return []
        query = self._where_calc(domain)
        self._apply_ir_rules(query, "read")
        from_clause, where_clause, where_clause_arguments = query.get_sql()
        parent_where = where_clause and (" WHERE %s" % where_clause) or ""
        parent_query = 'SELECT "%s".id FROM ' % self._table + from_clause + parent_where
        no_parent_clause = '"{table}"."{field}" IS NULL'.format(
            table=self._table, field=self._parent_name
        )
        no_access_clause = '"{table}"."{field}" NOT IN ({query})'.format(
            table=self._table, field=self._parent_name, query=parent_query
        )
        parent_clause = "({} OR {})".format(no_parent_clause, no_access_clause)
        order_by = self._generate_order_by(order, query)
        from_clause, where_clause, where_clause_params = query.get_sql()
        where_str = (
            where_clause
            and (" WHERE {} AND {}".format(where_clause, parent_clause))
            or (" WHERE %s" % parent_clause)
        )
        if count:
            # pylint: disable=sql-injection
            query_str = "SELECT count(1) FROM " + from_clause + where_str
            self._cr.execute(query_str, where_clause_params)
            return self._cr.fetchone()[0]
        limit_str = limit and " limit %s" or ""
        offset_str = offset and " offset %s" or ""
        query_str = (
            'SELECT "%s".id FROM ' % (self._table)
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

    @api.model
    def search_childs(
        self, parent_id, domain=False, offset=0, limit=None, order=None, count=False
    ):
        """This method finds the direct child elements of the parent
        record for a given search query.

        :param parent_id: the integer representing the ID of the parent record
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
        domain = self._build_search_childs_domain(parent_id, domain=domain)
        return self.search(domain, offset=offset, limit=limit, order=order, count=count)

    @api.model
    def search_read_childs(
        self, parent_id, domain=False, fields=None, offset=0, limit=None, order=None
    ):
        """This method finds the direct child elements of the parent
        record for a given search query.

        :param parent_id: the integer representing the ID of the parent record
        :param domain: a search domain <reference/orm/domains> (default: empty list)
        :param fields: a list of fields to read (default: all fields of the model)
        :param offset: the number of results to ignore (default: none)
        :param limit: maximum number of records to return (default: all)
        :param order: a string to define the sort order of the query (default: none)
        :returns: the top level elements for the given search query
        """
        if not domain:
            domain = []
        domain = self._build_search_childs_domain(parent_id, domain=domain)
        return self.search_read(
            domain=domain, fields=fields, offset=offset, limit=limit, order=order
        )
