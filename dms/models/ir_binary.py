# Copyright 2024 Subteno - Timothée Vannier (https://www.subteno.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import models


class IrBinary(models.AbstractModel):
    _inherit = "ir.binary"

    def _find_record_check_access(self, record, access_token):
        if record._name in ("dms.file", "dms.directory"):
            if record.sudo().check_access_token(access_token):
                # sudo because the user might not usually have access to the record but
                # now the token is valid.
                # Used to display the icon in the portal.
                return record.sudo()

        return super()._find_record_check_access(record, access_token)
