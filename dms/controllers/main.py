# Copyright 2017-2019 MuK IT GmbH
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import http
from odoo.http import request


class OnboardingController(http.Controller):
    @http.route("/config/dms.forbidden_extensions", type="json", auth="user")
    def forbidden_extensions(self, **_kwargs):
        params = request.env["ir.config_parameter"].sudo()
        return {
            "forbidden_extensions": params.get_param(
                "dms.forbidden_extensions", default=""
            )
        }
