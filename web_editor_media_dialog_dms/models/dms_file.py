# Copyright 2024 Tecnativa - Carlos Roca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models


class DmsFile(models.Model):
    _inherit = "dms.file"

    def get_access_token(self):
        """Return the access token used to share the file with public users.

        Access to the token is only granted to users that can read the file,
        as the token is written in sudo mode.
        """
        self.ensure_one()
        self.check_access("read")
        return self._portal_ensure_token()
