# Copyright 2026 Tecnativa - Adasat Torres
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _, fields, models


class DmsAction(models.Model):
    _inherit = "dms.action"

    kind = fields.Selection(
        selection_add=[("create_invoice", "Create Invoice")],
        ondelete={"create_invoice": "set default"},
        default="server_action",
    )

    move_type = fields.Selection(
        selection=[
            ("in_invoice", "Vendor Bill"),
            ("out_invoice", "Customer Invoice"),
            ("in_refund", "Vendor Credit Note"),
            ("out_refund", "Customer Credit Note"),
        ],
        string="Invoice Type",
        default="out_invoice",
    )

    journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Journal",
        domain=[("type", "in", ["sale", "purchase"])],
        help="Journal to use for the invoice creation",
    )

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner",
        help="Partner to use for the invoice creation",
    )

    account_move_id = fields.Many2one(
        comodel_name="account.move",
        string="Invoice",
        help="Invoice created by this action",
    )

    def _execute_create_invoice(self, file):
        """Create an invoice for the given file."""
        self.ensure_one()
        if not self.journal_id:
            raise ValueError(_("Journal is not set for this action."))
        if not self.account_move_id:
            self._create_invoice(file)
        return {
            "type": "ir.actions.act_window",
            "name": self.account_move_id.name,
            "res_model": "account.move",
            "view_mode": "form",
            "views": [(False, "form")],
            "res_id": self.account_move_id.id,
        }

    def _create_invoice(self, file):
        invoice = self.env["account.move"].create(
            {
                "move_type": self.move_type,
                "partner_id": self.partner_id.id,
                "journal_id": self.journal_id.id,
            }
        )
        attachment = self.env["ir.attachment"].create(
            {
                "name": file.name,
                "type": "binary",
                "datas": file.with_context(bin_size=False).content,
                "mimetype": file.mimetype,
                "res_model": "account.move",
                "res_id": invoice.id,
            }
        )
        invoice.write({"message_main_attachment_id": attachment.id})
        # Link the created invoice to the action
        self.account_move_id = invoice.id
