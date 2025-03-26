from odoo import api, models


class File(models.Model):
    _inherit = "dms.file"

    @api.model
    def create(self, vals):
        document = super().create(vals)
        # Find a matching workflow rule
        rule = self.env["dms.workflow.rule"].search(
            [("dms_exemption_folder", "=", document.directory_id.parent_id.id)], limit=1
        )
        if rule:
            rule.apply_rule(document)
        return document
