# Copyright 2017-2019 MuK IT GmbH
# Copyright 2020 RGB Consulting
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class DmsAccessGroups(models.Model):
    _name = "dms.access.group"
    _description = "Record Access Groups"

    _parent_store = True
    _parent_name = "parent_group_id"

    name = fields.Char(string="Group Name", required=True, translate=True)
    parent_path = fields.Char(string="Parent Path", index=True)
    perm_read = fields.Boolean(string="Read Access")
    perm_create = fields.Boolean(string="Create Access")
    perm_write = fields.Boolean(string="Write Access")
    perm_unlink = fields.Boolean(string="Unlink Access")
    directory_ids = fields.Many2many(
        comodel_name="dms.directory",
        relation="dms_directory_groups_rel",
        string="Directories",
        column1="gid",
        column2="aid",
        readonly=True,
    )
    count_users = fields.Integer(compute="_compute_users", string="Users", store=True)
    count_directories = fields.Integer(
        compute="_compute_count_directories", string="Count Directories"
    )
    parent_group_id = fields.Many2one(
        comodel_name="dms.access.group",
        string="Parent Group",
        ondelete="cascade",
        auto_join=True,
        index=True,
    )

    child_group_ids = fields.One2many(
        comodel_name="dms.access.group",
        inverse_name="parent_group_id",
        string="Child Groups",
    )
    group_ids = fields.Many2many(
        comodel_name="res.groups",
        relation="dms_access_group_groups_rel",
        column1="gid",
        column2="rid",
        string="Groups",
    )
    explicit_user_ids = fields.Many2many(
        comodel_name="res.users",
        relation="dms_access_group_explicit_users_rel",
        column1="gid",
        column2="uid",
        string="Explicit Users",
    )
    users = fields.Many2many(
        comodel_name="res.users",
        relation="dms_access_group_users_rel",
        column1="gid",
        column2="uid",
        string="Group Users",
        compute="_compute_users",
        store=True,
    )

    @api.depends("directory_ids")
    def _compute_count_directories(self):
        for record in self:
            record.count_directories = len(record.directory_ids)

    _sql_constraints = [
        ("name_uniq", "unique (name)", "The name of the group must be unique!")
    ]

    @api.model
    def default_get(self, fields_list):
        res = super(DmsAccessGroups, self).default_get(fields_list)
        if not self.env.context.get("groups_no_autojoin"):
            if "explicit_user_ids" in res and res["explicit_user_ids"]:
                res["explicit_user_ids"] = res["explicit_user_ids"] + [self.env.uid]
            else:
                res["explicit_user_ids"] = [self.env.uid]
        return res

    @api.depends(
        "parent_group_id",
        "parent_group_id.users",
        "group_ids",
        "group_ids.users",
        "explicit_user_ids",
    )
    def _compute_users(self):
        for record in self:
            users = record.mapped("group_ids.users")
            users |= record.mapped("explicit_user_ids")
            users |= record.mapped("parent_group_id.users")
            record.update({"users": users, "count_users": len(users)})
