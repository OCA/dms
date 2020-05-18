# Copyright 2020 Creu Blanca
# Copyright 2017-2019 MuK IT GmbH
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):

    _inherit = "res.config.settings"

    documents_binary_max_size = fields.Integer(
        string="Size", help="Defines the maximum upload size in MB. Default (25MB)"
    )

    documents_forbidden_extensions = fields.Char(
        string="Extensions",
        help="Defines a list of forbidden file extensions. (Example: 'exe,msi')",
    )

    # ----------------------------------------------------------
    # Functions
    # ----------------------------------------------------------

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        param = self.env["ir.config_parameter"].sudo()
        param.set_param("muk_web_utils.binary_max_size", self.documents_binary_max_size)
        param.set_param("dms.forbidden_extensions", self.documents_forbidden_extensions)
        return res

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env["ir.config_parameter"].sudo()
        res.update(
            documents_binary_max_size=int(
                params.get_param("muk_web_utils.binary_max_size", default=25)
            ),
            documents_forbidden_extensions=params.get_param(
                "dms.forbidden_extensions", default=""
            ),
        )
        return res
