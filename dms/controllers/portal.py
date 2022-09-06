# Copyright 2020-2021 Tecnativa - Víctor Martínez
import base64

from odoo import _, http
from odoo.http import request
from odoo.osv.expression import OR

from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.web.controllers.main import content_disposition, ensure_db


class CustomerPortal(CustomerPortal):
    def _dms_check_access(self, model, res_id, access_token=None):
        item = request.env[model].browse(res_id)
        if access_token:
            item = item.sudo()
            if not item.check_access_token(access_token):
                return False
        else:
            if not item.permission_read:
                return False
        return item

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if "dms_directory_count" in counters:
            ids = request.env["dms.directory"]._get_own_root_directories()
            values["dms_directory_count"] = len(ids)
        return values

    @http.route(["/my/dms"], type="http", auth="user", website=True)
    def portal_my_dms(
        self, sortby=None, filterby=None, search=None, search_in="name", **kw
    ):
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
        domain = [
            (
                "id",
                "in",
                request.env["dms.directory"]._get_own_root_directories(),
            )
        ]
        # search
        if search and search_in:
            search_domain = []
            if search_in == "name":
                search_domain = OR([search_domain, [("name", "ilike", search)]])
            domain += search_domain
        # content according to pager and archive selected
        items = request.env["dms.directory"].search(domain, order=sort_br)
        request.session["my_dms_folder_history"] = items.ids
        # values
        values.update(
            {
                "dms_directories": items,
                "page_name": "dms_directory",
                "default_url": "/my/dms",
                "searchbar_sortings": searchbar_sortings,
                "searchbar_inputs": searchbar_inputs,
                "search_in": search_in,
                "sortby": sortby,
                "filterby": filterby,
                "access_token": None,
            }
        )
        return request.render("dms.portal_my_dms", values)

    @http.route(
        ["/my/dms/directory/<int:dms_directory_id>"],
        type="http",
        auth="public",
        website=True,
    )
    def portal_my_dms_directory(
        self,
        dms_directory_id=False,
        sortby=None,
        filterby=None,
        search=None,
        search_in="name",
        access_token=None,
        **kw
    ):
        ensure_db()
        # operations
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
        domain = [("is_hidden", "=", False), ("parent_id", "=", dms_directory_id)]
        # search
        if search and search_in:
            search_domain = []
            if search_in == "name":
                search_domain = OR([search_domain, [("name", "ilike", search)]])
            domain += search_domain
        # content according to pager and archive selected
        if access_token:
            dms_directory_items = (
                request.env["dms.directory"].sudo().search(domain, order=sort_br)
            )
        else:
            dms_directory_items = request.env["dms.directory"].search(
                domain, order=sort_br
            )
        request.session["my_dms_folder_history"] = dms_directory_items.ids
        res = self._dms_check_access("dms.directory", dms_directory_id, access_token)
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
        if access_token:
            dms_file_items = (
                request.env["dms.file"].sudo().search(domain, order=sort_br)
            )
        else:
            dms_file_items = request.env["dms.file"].search(domain, order=sort_br)
        request.session["my_dms_file_history"] = dms_file_items.ids
        dms_parent_categories = dms_directory_sudo.sudo()._get_parent_categories(
            access_token
        )
        # values
        values = {
            "dms_directories": dms_directory_items,
            "page_name": "dms_directory",
            "default_url": "/my/dms",
            "searchbar_sortings": searchbar_sortings,
            "searchbar_inputs": searchbar_inputs,
            "search_in": search_in,
            "sortby": sortby,
            "filterby": filterby,
            "access_token": access_token,
            "dms_directory": dms_directory_sudo,
            "dms_files": dms_file_items,
            "dms_parent_categories": dms_parent_categories,
        }
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
        # operations
        res = self._dms_check_access("dms.file", dms_file_id, access_token)
        if not res:
            if access_token:
                return request.redirect("/")
            else:
                return request.redirect("/my")

        dms_file_sudo = res
        # It's necessary to prevent AccessError in ir_attachment .check() function
        if dms_file_sudo.attachment_id and request.env.user.has_group(
            "base.group_portal"
        ):
            dms_file_sudo = dms_file_sudo.sudo()
        filecontent = base64.b64decode(dms_file_sudo.content)
        content_type = ["Content-Type", "application/octet-stream"]
        disposition_content = [
            "Content-Disposition",
            content_disposition(dms_file_sudo.name),
        ]
        return request.make_response(filecontent, [content_type, disposition_content])
