from odoo import fields, models


class DMSWorkflowRule(models.Model):
    _name = "dms.workflow.rule"
    _description = "DMS Workflow Rule"

    name = fields.Char(required=True)
    dms_exemption_folder = fields.Many2one(
        "dms.directory", required=True, string="Exemption Workspace"
    )
    create_model = fields.Selection(
        selection=[("res.partner.exemption", "Avatax Exemption")], required=True
    )

    def apply_rule(self, document):
        """Apply workflow rule when a document is added to the folder."""
        if self.create_model == "res.partner.exemption":
            new_obj = self.env[self.create_model].create(
                {
                    "partner_id": document.create_uid.partner_id.id,
                    "document_link_id": document.id,
                }
            )
            return new_obj
        return False
