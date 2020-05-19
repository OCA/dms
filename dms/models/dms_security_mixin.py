# Copyright 2020 Creu Blanca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models
from odoo.exceptions import AccessError


class DmsSecurityMixin(models.AbstractModel):

    _name = "dms.security.mixin"
    _description = "DMS Security Mixin"

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

    def _filter_access(self, operation):
        if self.check_access_rights(operation, False):
            return self._filter_access_rules(operation)
        return self.env[self._name]

    def _filter_access_ids(self, operation):
        return self._filter_access(operation).ids

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
            return access_right and access_rule
        except AccessError:
            if raise_exception:
                raise
            return False
