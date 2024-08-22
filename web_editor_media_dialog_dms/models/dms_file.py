# Copyright 2024 Tecnativa - Carlos Roca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import _, models
from odoo.exceptions import AccessError
from odoo.tools import consteq


class File(models.Model):
    _inherit = "dms.file"

    def get_access_token(self):
        self.ensure_one()
        return self._portal_ensure_token()

    def validate_access(self, access_token):
        # Validate if token provided is correct for the record checked
        self.ensure_one()
        record_sudo = self.sudo()
        if access_token:
            tok = record_sudo.with_context(prefetch_fields=False).access_token
            valid_token = consteq(tok or "", access_token)
            if not valid_token:
                raise AccessError(_("Invalid access token"))
            return record_sudo
        return self
