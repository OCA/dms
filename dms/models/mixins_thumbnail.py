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

    custom_thumbnail = fields.Image(
        string="Custom Thumbnail",
        max_width=2048,
        max_height=2048,
        attachment=False,
        prefetch=False,
    )
    custom_thumbnail_medium = fields.Image(
        "Medium Custom Thumbnail",
        related="custom_thumbnail",
        max_width=512,
        max_height=512,
        prefetch=False,
    )
    custom_thumbnail_small = fields.Image(
        "Small Custom Thumbnail",
        related="custom_thumbnail",
        max_width=512,
        max_height=512,
        prefetch=False,
    )

    thumbnail = fields.Image(
        compute="_compute_thumbnail",
        string="Thumbnail",
        max_width=2048,
        max_height=2048,
        prefetch=False,
    )

    thumbnail_medium = fields.Image(
        "Medium Thumbnail",
        related="thumbnail",
        max_width=512,
        max_height=512,
        prefetch=False,
    )

    thumbnail_small = fields.Image(
        "SmallThumbnail",
        related="thumbnail",
        max_width=512,
        max_height=512,
        prefetch=False,
    )

    # ----------------------------------------------------------
    # Helper
    # ----------------------------------------------------------

    @api.model
    def _get_thumbnail_placeholder_image(self, size, name):
        path = self._get_thumbnail_path(size, name)
        with open(path, "rb") as image:
            return base64.b64encode(image.read())

    @api.model
    def _get_thumbnail_path(self, size, name):
        folders = ["static", "lib", "img", "thumbnails"]
        path = get_resource_path("dms", *folders, name)
        if not os.path.isfile(path):
            path = get_resource_path("dms", *folders, "file_unkown.svg")
        return path

    def _get_thumbnail_placeholder_name(self):
        return "folder.svg"

    @api.depends("custom_thumbnail")
    def _compute_thumbnail(self):
        for record in self:
            if record.custom_thumbnail:
                record.thumbnail = record.custom_thumbnail
            else:
                record.thumbnail = self._get_thumbnail_placeholder_image(
                    "original", record._get_thumbnail_placeholder_name()
                )
