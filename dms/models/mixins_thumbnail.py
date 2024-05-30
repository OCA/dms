# Copyright 2017-2019 MuK IT GmbH.
# Copyright 2020 Creu Blanca
# Copyright 2024 Subteno - Timothée Vannier (https://www.subteno.com).
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import os

from odoo import api, fields, models
from odoo.tools.misc import file_path


class Thumbnail(models.AbstractModel):
    _name = "dms.mixins.thumbnail"
    _inherit = "image.mixin"
    _description = "DMS thumbnail and icon mixin"

    icon_url = fields.Char(string="Icon URL", compute="_compute_icon_url")

    def _get_icon_disk_path(self):
        """Get the local disk path to record icon."""
        name = self._get_icon_placeholder_name()
        folders = ["dms", "static", "icons"]

        try:
            path = file_path(os.path.join(*folders, name))
        except FileNotFoundError:
            return file_path(os.path.join(*folders, "file_unknown.svg"))

        return path or file_path(os.path.join(*folders, "file_unknown.svg"))

    def _get_icon_placeholder_name(self):
        return "folder.svg"

    def _get_icon_url(self):
        """Obtain URL to record icon."""
        local_path = self._get_icon_disk_path()
        icon_name = os.path.basename(local_path)
        return "/dms/static/icons/%s" % icon_name

    @api.depends("image_128")
    def _compute_icon_url(self):
        """Get icon static file URL."""
        for one in self:
            # Get URL to thumbnail or to the default icon by file extension
            one.icon_url = (
                f"/web/image/{one._name}/{one.id}/image_128/128x128?crop=1"
                if one.image_128
                else f"{one._get_icon_url()}?crop=1"
            )
