# Copyright 2020 Tecnativa - Víctor Martínez
import base64
import logging

from odoo import _, http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.osv.expression import OR

from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.web.controllers.main import content_disposition, ensure_db

_logger = logging.getLogger(__name__)


class CustomerPortal(CustomerPortal):
    def _dms_check_access(self, model, res_id, access_token=None):
        try:
            item_sudo = request.env[model].sudo().browse([res_id])
        except (AccessError, MissingError):
            return False

        if access_token:
            if not item_sudo.check_access_token(access_token):
                return False
        else:
            if not item_sudo.sudo(request.env.user.id).check_access("read", False):
                return False

        return item_sudo

    def _prepare_portal_layout_values(self):
        values = super()._prepare_portal_layout_values()
        ids = request.env["dms.directory"]._get_own_root_directories(
            request.env.user.id
        )
        values.update({"dms_directory_count": len(ids)})
        return values

    @http.route(
        ["/my/dms/", "/my/dms/directory/<int:dms_directory_id>"],
        type="http",
        auth="public",
        website=True,
    )
    def portal_my_dms(
        self,
        dms_directory_id=False,
        sortby=None,
        filterby=None,
        search=None,
        search_in="name",
        access_token=None,
        **kw
    ):
        """Process user's consent acceptance or rejection."""
        ensure_db()
        try:
            # If there's a website, we need a user to render the template
            request.uid = request.website.user_id.id
        except AttributeError:
            # If there's no website, the default is OK
            pass
        # operations
        values = self._prepare_portal_layout_values()
        searchbar_sortings = {"name": {"label": _("Name"), "order": "name asc"}}
        # default sortby br
        if not sortby:
            sortby = "name"
        sort_br = searchbar_sortings[sortby]["order"]
        # search
        searchbar_inputs = {
            "name": {"input": "name", "label": _("Name")},
        }
        if not filterby:
            filterby = "name"
        # domain
        if not dms_directory_id:
            domain = [
                (
                    "id",
                    "in",
                    request.env["dms.directory"]._get_own_root_directories(
                        request.env.user.id
                    ),
                )
            ]
        else:
            domain = [("is_hidden", "=", False), ("parent_id", "=", dms_directory_id)]
        # search
        if search and search_in:
            search_domain = []
            if search_in == "name":
                search_domain = OR([search_domain, [("name", "ilike", search)]])
            domain += search_domain
        # content according to pager and archive selected
        items = (
            request.env["dms.directory"]
            .sudo(request.env.user.id)
            .search(domain, order=sort_br)
        )
        request.session["my_dms_folder_history"] = items.ids
        # values
        values.update(
            {
                "dms_directories": items.sudo(),
                "page_name": "dms_directory",
                "default_url": "/my/dms/directories",
                "searchbar_sortings": searchbar_sortings,
                "searchbar_inputs": searchbar_inputs,
                "search_in": search_in,
                "sortby": sortby,
                "filterby": filterby,
                "access_token": access_token,
            }
        )
        if dms_directory_id:
            # check_access
            res = self._dms_check_access(
                "dms.directory", dms_directory_id, access_token
            )
            if not res:
                if access_token:
                    return request.redirect("/")
                else:
                    return request.redirect("/my")

            dms_directory_sudo = res
            # dms_files_count
            domain = [
                ("is_hidden", "=", False),
                ("directory_id", "=", dms_directory_id),
            ]
            # search
            if search and search_in:
                search_domain = []
                if search_in == "name":
                    search_domain = OR([search_domain, [("name", "ilike", search)]])
                domain += search_domain
            # items
            items = (
                request.env["dms.file"]
                .sudo(request.env.user.id)
                .search(domain, order=sort_br)
            )
            request.session["my_dms_file_history"] = items.ids
            dms_parent_categories = dms_directory_sudo.sudo(
                request.env.user.id
            )._get_parent_categories(access_token)
            values.update(
                {
                    "dms_directory": dms_directory_sudo,
                    "dms_files": items.sudo(),
                    "dms_parent_categories": dms_parent_categories,
                }
            )
        return request.render("dms.portal_my_dms", values)

    @http.route(
        ["/my/dms/file/<int:dms_file_id>/download"],
        type="http",
        auth="public",
        website=True,
    )
    def portal_my_dms_file_download(self, dms_file_id, access_token=None, **kw):
        """Process user's consent acceptance or rejection."""
        ensure_db()
        try:
            # If there's a website, we need a user to render the template
            request.uid = request.website.user_id.id
        except AttributeError:
            # If there's no website, the default is OK
            pass
        # operations
        res = self._dms_check_access("dms.file", dms_file_id, access_token)
        if not res:
            if access_token:
                return request.redirect("/")
            else:
                return request.redirect("/my")

        dms_file_sudo = res
        filecontent = base64.b64decode(dms_file_sudo.content)
        content_type = ["Content-Type", "application/octet-stream"]
        disposition_content = [
            "Content-Disposition",
            content_disposition(dms_file_sudo.name),
        ]
        return request.make_response(filecontent, [content_type, disposition_content])
