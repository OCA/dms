# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class DmsFieldTemplate(models.Model):
    _inherit = "dms.field.template"

    def _create_dms_directory(self):
        """Custom method to define the directory automatically in demo data avoiding
        error if it already exists."""
        self.ensure_one()
        if not self.dms_directory_ids:
            self.with_context(
                res_model=self._name, res_id=self.id
            ).create_dms_directory()
