# Copyright 2021 Tecnativa - Jairo Llopis
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    for model in ("dms.file", "dms.directory"):
        _logger.info("Computing stored custom thumbnails for model %s", model)
        records = env[model].search([("custom_thumbnail", "!=", False)])
        records._compute_custom_thumbnail()
