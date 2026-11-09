# Copyright 2024 Tecnativa - Carlos Roca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models


class IrBinary(models.AbstractModel):
    _inherit = "ir.binary"

    def _find_record_check_access(self, record, access_token, field=None):
        # The method is overridden to allow access to the media attached to the
        # dms.file records using an access_token.
        if record._name == "dms.file":
            return record.validate_access(access_token)
        return super()._find_record_check_access(record, access_token, field=field)
