from odoo import models
from odoo.http import request

DMS_UI_COLOR_SCHEMES = {
    "purple",
    "teal",
    "charcoal",
    "blue",
    "green",
    "red",
    "cyan",
    "amber",
}


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _dms_ui_color_scheme(cls):
        if not request.session.uid:
            return "purple"
        user = request.env["res.users"].sudo().browse(request.session.uid).exists()
        if not user:
            return "purple"
        scheme = user.dms_ui_custom_theme
        return scheme if scheme in DMS_UI_COLOR_SCHEMES else "purple"

    @classmethod
    def _set_dms_ui_color_scheme(cls, response):
        scheme = cls._dms_ui_color_scheme()
        if request.httprequest.cookies.get("dms_ui_color_scheme") != scheme:
            response.set_cookie("dms_ui_color_scheme", scheme)
        if request.httprequest.cookies.get("dms_ui_custom_theme"):
            response.delete_cookie("dms_ui_custom_theme")

    @classmethod
    def _post_dispatch(cls, response):
        cls._set_dms_ui_color_scheme(response)
        return super()._post_dispatch(response)
