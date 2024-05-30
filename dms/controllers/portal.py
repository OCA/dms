# Copyright 2020-2021 Tecnativa - Víctor Martínez
# Copyright 2024 Subteno - Timothée VANNIER (https://www.subteno.com).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
import base64
from typing import Optional  # noqa # pylint: disable=unused-import

from odoo import _, http
from odoo.http import content_disposition, request
from odoo.osv.expression import OR

from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.web.controllers.utils import ensure_db


class CustomerPortal(CustomerPortal):
    def _dms_check_access(self, model, res_id, access_token=None):
        """
        Check access to the record.

        :param str model: model
        :param int res_id: res_id
        :param Optional[str] access_token: access_token

        :return: item
        """
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
        """
        Display the main page for the DMS module.

        :param Optional[str] sortby: The field to sort by
        :param Optional[str] filterby: The field to filter by
        :param Optional[str] search: The search term
        :param Optional[str] search_in: The field to search in

        :return: response
        :rtype: odoo.http.Response
        """
        values = self._prepare_portal_layout_values()
        (
            filterby,
            searchbar_inputs,
            searchbar_sortings,
            sort_order,
            sortby,
        ) = self._searchbar_data(filterby, sortby)
        # domain
        domain = [
            ("id", "in", request.env["dms.directory"]._get_own_root_directories()),
        ]
        # search
        if search and search_in == "name":
            domain += OR([[], [("name", "ilike", search)]])
        # content according to pager and archive selected
        items = request.env["dms.directory"].search(domain, order=sort_order)
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
        **kw,
    ):
        """
        Display the content of a directory.

        :param Optional[int] dms_directory_id: dms_directory_id
        :param Optional[str] sortby: sortby
        :param Optional[str] filterby: filterby
        :param Optional[str] search: search
        :param Optional[str] search_in: search_in
        :param Optional[str] access_token: access_token

        :return: response
        :rtype: odoo.http.Response
        """
        ensure_db()
        # operations
        (
            filterby,
            searchbar_inputs,
            searchbar_sortings,
            sort_order,
            sortby,
        ) = self._searchbar_data(filterby, sortby)
        dms_directory_items, res = self._get_directories(
            access_token, dms_directory_id, search, search_in, sort_order
        )
        if not res:
            return request.redirect("/" if access_token else "/my")

        dms_directory_sudo = res
        # dms_files_count
        dms_file_items = self._get_files(
            access_token, dms_directory_id, search, search_in, sort_order
        )

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

    def _get_files(self, access_token, dms_directory_id, search, search_in, sort_br):
        """
        Get files from dms_directory_id

        :param Optional[str] access_token: access_token
        :param int dms_directory_id: dms_directory_id
        :param Optional[str] search: search
        :param Optional[str] search_in: search_in
        :param str sort_br: sort_br

        :return: dms_file_items
        :rtype: odoo.model.dms_file
        """
        if not dms_directory_id:
            return request.env["dms.file"]
        file_domain = [
            ("is_hidden", "=", False),
            ("directory_id", "=", dms_directory_id),
        ]
        # search
        if search and search_in == "name":
            file_domain.append(("name", "ilike", search))

        # items
        file_model = request.env["dms.file"]
        is_access_token_valid = file_model.check_access_token(access_token)
        file_model = file_model.sudo() if is_access_token_valid else file_model
        dms_file_items = file_model.search(file_domain, order=sort_br)
        request.session["my_dms_file_history"] = dms_file_items.ids
        return dms_file_items

    def _get_directories(
        self, access_token, dms_directory_id, search, search_in, sort_order
    ):
        """
        Get directories from dms_directory_id

        :param Optional[str] access_token: access_token
        :param int dms_directory_id: dms_directory_id
        :param Optional[str] search: search
        :param Optional[str] search_in: search_in
        :param str sort_order: sort_br

        :return: dms_directory_items, res
        :rtype: tuple[odoo.model.dms_directory, bool|odoo.model.dms_directory]
        """
        # domain
        domain = [("is_hidden", "=", False), ("parent_id", "=", dms_directory_id)]
        # search
        if search and search_in:
            domain.append(("name", "ilike", search))

        # content according to pager and archive selected
        directory_model = request.env["dms.directory"]
        directory_to_check = directory_model.browse(dms_directory_id)
        is_access_token_valid = directory_to_check.check_access_token(access_token)
        directory_model = (
            directory_model.sudo() if is_access_token_valid else directory_model
        )
        dms_directory_items = directory_model.search(domain, order=sort_order)

        request.session["my_dms_folder_history"] = dms_directory_items.ids
        res = self._dms_check_access("dms.directory", dms_directory_id, access_token)
        return dms_directory_items, res

    def _searchbar_data(self, filterby, sortby):
        """
        Prepare searchbar data for portal.

        :param str filterby: filterby
        :param str sortby: sortby

        :return: filterby, searchbar_inputs, searchbar_sortings, sort_order,
        sortby
        :rtype: tuple[str, dict, dict, str, str]
        """
        searchbar_sortings = {"name": {"label": _("Name"), "order": "name asc"}}
        # default sortby
        if not sortby:
            sortby = "name"
        sort_order = searchbar_sortings[sortby]["order"]
        # search
        searchbar_inputs = {
            "name": {"input": "name", "label": _("Name")},
        }
        if not filterby:
            filterby = "name"
        return (
            filterby,
            searchbar_inputs,
            searchbar_sortings,
            sort_order,
            sortby,
        )

    @http.route(
        ["/my/dms/file/<int:dms_file_id>/download"],
        type="http",
        auth="public",
        website=True,
    )
    def portal_my_dms_file_download(self, dms_file_id, access_token=None, **kw):
        """
        Download a file.

        :param int dms_file_id: dms_file_id
        :param Optional[str] access_token: access_token

        :return: response
        :rtype: odoo.http.Response
        """
        ensure_db()
        res = self._dms_check_access("dms.file", dms_file_id, access_token)
        if not res:
            if access_token:
                return request.redirect("/")
            return request.redirect("/my")

        if res.attachment_id and request.env.user.has_group("base.group_portal"):
            res = res.sudo()
        file_content = base64.b64decode(res.content)
        content_type = ("Content-Type", "application/octet-stream")
        disposition_content = (
            "Content-Disposition",
            content_disposition(res.name),
        )
        return request.make_response(file_content, [content_type, disposition_content])
