# Copyright 2021 Tecnativa - Jairo Llopis
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from openupgradelib import openupgrade, openupgrade_90


def convert_binary_fields_to_attachment(env):
    """Convert old user-provided thumbnails to attachments."""
    column = openupgrade.get_legacy_name("custom_thumbnail")
    spec = {
        "dms.file": [("image_1920", column)],
        "dms.directory": [("image_1920", column)],
    }
    openupgrade_90.convert_binary_field_to_attachment(env, spec)
    # Force rewrite to force resizing and recomputing smaller thumbnails
    env["dms.file"].search([])._compute_image_1920()
    for record in env["dms.file"].search(
        [("image_1920", "!=", False), "!", ("mimetype", "=ilike", "image/%")]
    ):
        record.image_1920 = record.image_1920
    for record in env["dms.directory"].search([("image_1920", "!=", False)]):
        record.image_1920 = record.image_1920


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    convert_binary_fields_to_attachment(env)
