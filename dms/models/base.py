# Copyright 2021 Tecnativa - Jairo Llopis
# Copyright 2024 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import models


class Base(models.AbstractModel):
    _inherit = "base"

    def unlink(self):
        """Cascade DMS related resources removal.
        Avoid executing in ir.* models (ir.mode, ir.model.fields, etc), in transient
        models and in the models we want to check."""
        result = super().unlink()
        if (
            not self._name.startswith("ir.")
            and not self.is_transient()
            and self._name not in ("dms.file", "dms.directory")
        ):
            domain = [("res_model", "=", self._name), ("res_id", "in", self.ids)]
            self.env["dms.file"].sudo().search(domain).unlink()
            self.env["dms.directory"].sudo().search(domain).unlink()
        return result
