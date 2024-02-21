# Copyright 2017-2020 MuK IT GmbH
# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, exceptions, fields, models


class DmsFile(models.Model):
    _name = "dms.file"
    _inherit = ["dms.file", "base.revision"]

    name = fields.Char(
        tracking=True,
    )
    directory_id = fields.Many2one(
        tracking=True,
    )
    storage_id = fields.Many2one(
        tracking=True,
    )
    extension = fields.Char(
        tracking=True,
    )
    mimetype = fields.Char(
        tracking=True,
    )
    category_id = fields.Many2one(
        tracking=True,
    )
    current_revision_id = fields.Many2one(
        comodel_name="dms.file",
        readonly=True,
    )
    old_revision_ids = fields.One2many(
        comodel_name="dms.file",
    )
    has_versioning = fields.Boolean(
        string="Has Versioning",
        tracking=True,
    )
    can_edit_has_versioning = fields.Boolean(
        compute="_compute_can_edit_has_versioning",
        default=True,
    )
    origin_id = fields.Many2one(
        comodel_name="dms.file",
    )
    all_revision_ids = fields.One2many(
        comodel_name="dms.file",
        inverse_name="origin_id",
        readonly=True,
        domain=["|", ("active", "=", False), ("active", "=", True)],
        context={"active_test": False},
    )
    all_revision_count = fields.Integer(
        compute="_compute_all_revision_count",
    )
    parent_id = fields.Many2one(
        comodel_name="dms.file",
    )
    has_current_revision = fields.Boolean(
        compute="_compute_has_current_revision", store=True
    )

    # (overwrite) sql_constraints revision_unique from module base_revision
    _sql_constraints = [
        (
            "revision_unique",
            "Check(1=1)",
            "Reference and revision must be unique.",
        )
    ]

    @api.constrains("unrevisioned_name", "revision_number", "directory_id")
    def check_unique_name_revision_number(self):
        for rec in self:
            if rec.origin_id:
                res = self.search_count(
                    [
                        ("unrevisioned_name", "=", rec.unrevisioned_name),
                        ("revision_number", "=", rec.revision_number),
                        ("directory_id", "=", rec.directory_id.id),
                        "|",
                        ("active", "=", False),
                        ("active", "=", True),
                    ]
                )
                if res > 1:
                    raise exceptions.UserError(
                        _("Reference and revision must be unique in a directory.")
                    )

    @api.constrains("active", "origin_id")
    def check_unique_active_file(self):
        for rec in self:
            if rec.origin_id:
                res = self.search_count(
                    [
                        ("origin_id", "=", rec.origin_id.id),
                    ]
                )
                if res > 1:
                    raise exceptions.UserError(
                        _(
                            'Found more active version of file "%s".'
                            % rec.origin_id.name
                        )
                    )

    @api.constrains("revision_number", "origin_id")
    def check_unique_origin_revision_number(self):
        for rec in self:
            if rec.origin_id:
                res = self.search_count(
                    [
                        ("origin_id", "=", rec.origin_id.id),
                        ("revision_number", "=", rec.revision_number),
                        "|",
                        ("active", "=", False),
                        ("active", "=", True),
                    ]
                )
                if res > 1:
                    raise exceptions.UserError(
                        _('Revision number "%s" must be unique.' % rec.revision_number)
                    )

    def _compute_can_edit_has_versioning(self):
        can_edit = self.user_has_groups("dms_version.group_dms_version_user")
        for rec in self:
            rec.can_edit_has_versioning = can_edit

    @api.depends("current_revision_id", "current_revision_id.active")
    def _compute_has_current_revision(self):
        for rec in self:
            rec.has_current_revision = False
            if rec.current_revision_id and rec.current_revision_id.active:
                rec.has_current_revision = True
            elif not rec.current_revision_id and rec.has_versioning and rec.active:
                rec.has_current_revision = True

    @api.depends("all_revision_ids")
    def _compute_all_revision_count(self):
        for rec in self:
            rec.all_revision_count = len(rec.origin_id.all_revision_ids) - 1

    @api.onchange("directory_id")
    def _onchange_directory_id(self):
        for rec in self:
            if rec.directory_id:
                rec.has_versioning = rec.directory_id.has_versioning

    def action_view_revision(self):
        self.ensure_one()
        action = self.env.ref("dms_version.action_dms_revisions_file")
        res = action.read()[0]
        res["domain"] = [
            "&",
            ("id", "in", self.origin_id.all_revision_ids.ids),
            "|",
            ("active", "=", False),
            ("active", "=", True),
        ]
        return res

    @api.model
    def create(self, values):
        res = super().create(values)
        if "origin_id" not in values:
            res.origin_id = res
        return res

    def write(self, vals):
        if (
            not self.env.context.get("restore_old_revision", False)
            and "active" in vals
            and vals["active"]
        ):
            raise exceptions.UserError(
                _("Please use the restore button to activate this revision.")
            )
        if vals.get("content"):
            versions = self.filtered(lambda x: x.has_versioning)
            super(DmsFile, versions).write({"active": False})
            action = versions.with_context(new_vals=vals).create_revision()
            res = self.search(action["domain"])
            if versions.ids == self.ids:
                return res
            else:
                return super(
                    DmsFile, self.filtered(lambda x: not x.has_versioning)
                ).write(vals)
        res = super().write(vals)
        return res

    def _get_new_rev_data(self, new_rev_number):
        self.ensure_one()
        res = super()._get_new_rev_data(new_rev_number)
        new_vals = self.env.context.get("new_vals", False)
        if new_vals:
            res.update(new_vals)
        res["origin_id"] = self.origin_id.id
        res["parent_id"] = self.id
        res["active"] = True
        max_new_rev_number = (
            max(self.origin_id.all_revision_ids.mapped("revision_number")) + 1
        )
        res["revision_number"] = max_new_rev_number
        return res

    def action_restore_old_revision(self):
        self.ensure_one()
        rec_link = self.get_html_link()
        msg1 = _("This version is restored.")
        if self.current_revision_id.active:
            current_version_link = self.current_revision_id.get_html_link()
            msg1 += _("\nThe version %s is now archived.") % (current_version_link,)
            msg2 = _("The version %s is restored. This version is now archived.") % (
                rec_link,
            )
            self.current_revision_id.message_post(body=msg2)
        self.message_post(body=msg1)
        if self.origin_id.id not in (self.current_revision_id.id, self.id):
            msg3 = _("The version %s is restored.") % (rec_link)
            if self.current_revision_id.active:
                msg3 += _(" The version %s is now archived.") % (current_version_link)
            self.origin_id.message_post(body=msg3)
        self.current_revision_id.active = False
        self.active = True
        self.origin_id.all_revision_ids.write({"current_revision_id": self.id})
        self.current_revision_id.write({"current_revision_id": False})

    def copy_revision_with_context(self):
        new_revision = super().copy_revision_with_context()
        new_rev_number = new_revision.revision_number
        new_revision.write(
            {
                "name": "%s-%02d" % (self.unrevisioned_name, new_rev_number),
            }
        )
        return new_revision

    def get_html_link(self):
        self.ensure_one()
        res = '<a href="#" data-oe-model="dms.file" data-oe-id="%s">%s</a>' % (
            self.id,
            self.name,
        )
        return res

    # (override) function create_revistion() from base_revision
    def create_revision(self):
        revision_ids = []
        # Looping over records
        for rec in self:
            # Calling  Copy method
            copied_rec = rec.copy_revision_with_context()
            if hasattr(self, "message_post"):
                # (change) add a link for opening the copied record
                msg = _("This revision is created from file %s.") % (
                    rec.get_html_link()
                )
                copied_rec.message_post(body=msg)
                msg = _("A new revision %s is created from this file.") % (
                    copied_rec.get_html_link()
                )
                rec.message_post(body=msg)
                if rec.id != rec.origin_id.id:
                    msg = _("A new revision %s is created from file %s.") % (
                        copied_rec.get_html_link(),
                        rec.get_html_link(),
                    )
                    rec.origin_id.message_post(body=msg)
            revision_ids.append(copied_rec.id)
        action = {
            "type": "ir.actions.act_window",
            "view_mode": "tree,form",
            "name": _("New Revisions"),
            "res_model": self._name,
            "domain": [("id", "in", revision_ids)],
            "target": "current",
        }
        return action
