# Copyright 2017-2019 MuK IT GmbH
# Copyright 2026 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import base64
import json
import unicodedata

from odoo import _, http
from odoo.exceptions import AccessError
from odoo.http import request

from odoo.addons.web.controllers.binary import clean


class OnboardingController(http.Controller):
    @http.route("/config/dms.forbidden_extensions", type="json", auth="user")
    def forbidden_extensions(self, **_kwargs):
        params = request.env["ir.config_parameter"].sudo()
        return {
            "forbidden_extensions": params.get_param(
                "dms.forbidden_extensions", default=""
            )
        }

    @http.route("/web/binary/upload_dms_file", type="http", auth="user")
    def upload_dms_file(self, ufile, directory_id, callback=None):
        """Similar to the web upload_attachment() method, but customized to
        directly create dms.file records.
        """
        directory_id = int(directory_id)
        files = request.httprequest.files.getlist("ufile")
        Model = request.env["dms.file"]
        out = """<script language="javascript" type="text/javascript">
                    var win = window.top.window;
                    win.jQuery(win).trigger(%s, %s);
                </script>"""
        args = []
        for ufile in files:
            filename = ufile.filename
            if request.httprequest.user_agent.browser == "safari":
                # Safari sends NFD UTF-8 (where é is composed by 'e' and [accent])
                # we need to send it the same stuff, otherwise it'll fail
                filename = unicodedata.normalize("NFD", ufile.filename)
            try:
                dms_file = Model.create(
                    {
                        "directory_id": directory_id,
                        "name": filename,
                        "content": base64.b64encode(ufile.read()),
                    }
                )
            except AccessError:
                args.append({"error": _("You are not allowed to upload a file here.")})
            except Exception:
                args.append({"error": _("Something horrible happened")})
            else:
                args.append(
                    {
                        "filename": clean(filename),
                        "mimetype": dms_file.mimetype,
                        "id": dms_file.id,
                        "size": dms_file.size,
                    }
                )
        return (
            out % (json.dumps(clean(callback)), json.dumps(args))
            if callback
            else json.dumps(args)
        )
