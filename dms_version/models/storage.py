# Copyright 2017-2020 MuK IT GmbH
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

import bsdiff4


class Storage(models.Model):

    _inherit = "dms.storage"

    has_versioning = fields.Boolean(
        string="Active Versioning",
        default=False,
        help="Indicates if files have an active version control.",
    )

    stored_versions = fields.Integer(
        string="Saved Versions",
        default=3,
        help="Indicates how many versions are saved per file.",
    )

    clean_versions = fields.Selection(
        selection=[("immediately", _("On Write")), ("autovacuum", _("On Autovacuum"))],
        string="Clean Versions",
        default="autovacuum",
    )

    compress_versions = fields.Boolean(
        string="Compress Versions",
        default=False,
        help="Compress versions to minimize the used space.",
    )

    incremental_versions = fields.Boolean(
        string="Only Save Changes",
        default=False,
        help="Only save the incremental changes between two versions.",
    )

    def action_clean_file_versions(self):
        versions = self.env["dms.version"].sudo()
        files = self.mapped("storage_file_ids").sudo()
        versions.clean_versions(files)

    def action_delete_file_versions(self):
        self.mapped("storage_file_ids.version_ids").sudo().unlink()

    @api.model
    def clean_file_versions(self):
        domain = [("has_versioning", "=", True), ("clean_versions", "=", "autovacuum")]
        self.search(domain).action_clean_file_versions()


    @api.constrains("has_versioning", "stored_versions")
    def _check_stored_versions(self):
        for record in self:
            if record.has_versioning and record.stored_versions <= 0:
                raise ValidationError(
                    _("There amount of saved versions needs to be greater than 0.")
                )

    @api.constrains("has_versioning", "clean_versions")
    def _check_clean_versions(self):
        for record in self:
            if record.has_versioning and not record.clean_versions:
                raise ValidationError(
                    _("A version cleaning setting has to be selected.")
                )
