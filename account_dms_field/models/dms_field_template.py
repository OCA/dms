from odoo import models


class DmsFieldTemplate(models.Model):
    _inherit = "dms.field.template"

    def _prepare_directory_vals(self, directory, record):
        vals = super()._prepare_directory_vals(directory, record)
        if "/" not in vals["name"]:
            return vals
        vals["name"] = vals["name"].replace("/", "-")
        return vals
