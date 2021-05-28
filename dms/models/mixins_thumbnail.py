# Copyright 2017-2019 MuK IT GmbH.
# Copyright 2020 Creu Blanca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64
import os

from odoo import api, fields, models
from odoo.modules.module import get_resource_path


class Thumbnail(models.AbstractModel):

    _name = "dms.mixins.thumbnail"
    _description = "Thumbnail Mixin"

    custom_thumbnail = fields.Binary(string="Custom Thumbnail", attachment=False)
    custom_thumbnail_medium = fields.Binary(
        string="Medium Custom Thumbnail",
        related="custom_thumbnail",
        attachment=True,
        store=True,
        max_width=128,
        max_height=128,
    )
    custom_thumbnail_small = fields.Binary(
        string="Small Custom Thumbnail",
        related="custom_thumbnail",
        attachment=True,
        store=True,
        max_width=64,
        max_height=64,
    )
    thumbnail = fields.Binary(compute="_compute_thumbnail", string="Thumbnail",)
    thumbnail_medium = fields.Binary(
        string="Medium Thumbnail", compute="_compute_thumbnail"
    )
    thumbnail_small = fields.Binary(
        string="Small Thumbnail", compute="_compute_thumbnail"
    )
    icon_url = fields.Char(string="Icon URL", compute="_compute_icon_url")

    # ----------------------------------------------------------
    # Helper
    # ----------------------------------------------------------

    @api.model
    def _get_thumbnail_placeholder_image(self, name):
        path = self._get_thumbnail_path(name)
        with open(path, "rb") as image:
            return base64.b64encode(image.read())

    @api.model
    def _get_thumbnail_path(self, name):
        folders = ["static", "lib", "img", "thumbnails"]
        path = get_resource_path("dms", *folders, name)
        if not os.path.isfile(path):
            path = get_resource_path("dms", *folders, "file_unknown.svg")
        return path

    def _get_thumbnail_placeholder_name(self):
        return "folder.svg"

    def _compute_icon_url(self):
        """Get icon static file URL."""
        for one in self:
            thumbnail_path = one._get_thumbnail_path(
                one._get_thumbnail_placeholder_name()
            )
            thumbnail_name = os.path.basename(thumbnail_path)
            one.icon_url = "/dms/static/lib/img/thumbnails/%s" % thumbnail_name

    @api.depends("custom_thumbnail_medium", "custom_thumbnail_small")
    def _compute_thumbnail(self):
        """Generate small thumbnails, with icon fallback.

        NEVER use ``thumbnail_*`` fields in list/kanban views, or things will
        slow down. Instead, use directly ``icon_url`` or ``custom_thumbnail_*``.

        It reflects ``custom_thumbnail_*`` fields if possible, but defaults to
        the mimetype icon.
        """
        for record in self:
            icon_fallback = record._get_thumbnail_placeholder_image(
                record._get_thumbnail_placeholder_name()
            )
            for field in ("thumbnail", "thumbnail_medium", "thumbnail_small"):
                record[field] = record["custom_%s" % field] or icon_fallback
