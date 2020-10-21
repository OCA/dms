# Copyright 2017-2019 MuK IT GmbH.
# Copyright 2020 Creu Blanca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64
import os

from odoo import api, fields, models, tools
from odoo.modules.module import get_resource_path


class Thumbnail(models.AbstractModel):

    _name = "dms.mixins.thumbnail"
    _description = "Thumbnail Mixin"

    custom_thumbnail = fields.Binary(
        string="Custom Thumbnail", attachment=False, prefetch=False,
    )
    custom_thumbnail_medium = fields.Binary(
        "Medium Custom Thumbnail", compute="_compute_custom_thumbnail", prefetch=False,
    )
    custom_thumbnail_small = fields.Binary(
        "Small Custom Thumbnail", compute="_compute_custom_thumbnail", prefetch=False,
    )

    thumbnail = fields.Binary(
        compute="_compute_thumbnail", string="Thumbnail", prefetch=False,
    )

    thumbnail_medium = fields.Binary(
        "Medium Thumbnail", compute="_compute_thumbnail", prefetch=False,
    )

    thumbnail_small = fields.Binary(
        "SmallThumbnail", compute="_compute_thumbnail", prefetch=False,
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
            path = get_resource_path("dms", *folders, "file_unkown.png")
        return path

    def _get_thumbnail_placeholder_name(self):
        return "folder.png"

    @api.depends("custom_thumbnail")
    def _compute_custom_thumbnail(self):
        for record in self:
            if not record.custom_thumbnail:
                record.custom_thumbnail_medium = False
                record.custom_thumbnail_small = False
            else:
                resized_images = tools.image_get_resized_images(
                    record.custom_thumbnail, return_big=True, avoid_resize_medium=True
                )
                record.custom_thumbnail_medium = resized_images["image_medium"]
                record.custom_thumbnail_small = resized_images["image_small"]

    @api.depends("custom_thumbnail")
    def _compute_thumbnail(self):
        for record in self:
            if record.custom_thumbnail:
                record.thumbnail = record.with_context(bin_size=False).custom_thumbnail
            else:
                record.thumbnail = self._get_thumbnail_placeholder_image(
                    "original", record._get_thumbnail_placeholder_name()
                )
            resized_images = tools.image_get_resized_images(
                record.thumbnail, return_big=True, avoid_resize_medium=True
            )
            record.thumbnail_medium = resized_images["image_medium"]
            record.thumbnail_small = resized_images["image_small"]
