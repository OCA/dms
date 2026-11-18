# Copyright 2026 Tecnativa - Adasat Torres
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import Command
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.addons.dms.tests.common import DocumentsBaseCase


@tagged("post_install", "-at_install")
class TestDmsActionInvoicing(DocumentsBaseCase, AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # The accounting test user also manages the DMS fixtures.
        cls.env.user.sudo().write(
            {"groups_id": [Command.link(cls.env.ref("dms.group_dms_manager").id)]}
        )
        cls.access_group.sudo().write(
            {"explicit_user_ids": [Command.link(cls.env.uid)]}
        )
        cls.storage = cls.create_storage()
        cls.directory = cls.create_directory(storage=cls.storage)
        cls.file = cls.create_file(directory=cls.directory)
        cls.partner = cls.env["res.partner"].create({"name": "Invoice partner"})
        cls.action = cls.env["dms.action"].create(
            {
                "name": "Create invoice",
                "kind": "create_invoice",
                "partner_id": cls.partner.id,
                "journal_id": cls.company_data["default_journal_sale"].id,
                "dms_directory_ids": [Command.link(cls.directory.id)],
            }
        )

    def test_default_move_type(self):
        self.assertEqual(self.action.move_type, "out_invoice")

    def test_create_invoice_types(self):
        for move_type in ("out_invoice", "in_invoice", "out_refund", "in_refund"):
            with self.subTest(move_type=move_type):
                journal_key = (
                    "default_journal_purchase"
                    if move_type.startswith("in_")
                    else "default_journal_sale"
                )
                action = self.action.copy(
                    {
                        "move_type": move_type,
                        "journal_id": self.company_data[journal_key].id,
                        "account_move_id": False,
                    }
                )
                result = action._execute_action(self.file)
                invoice = action.account_move_id
                self.assertTrue(invoice)
                self.assertEqual(invoice.move_type, move_type)
                self.assertEqual(invoice.partner_id, self.partner)
                self.assertEqual(invoice.journal_id, action.journal_id)
                self.assertEqual(invoice.state, "draft")
                self.assertEqual(result["type"], "ir.actions.act_window")
                self.assertEqual(result["res_model"], "account.move")
                self.assertEqual(result["view_mode"], "form")
                self.assertEqual(result["views"], [(False, "form")])
                self.assertEqual(result["res_id"], invoice.id)
                attachment = invoice.message_main_attachment_id
                self.assertTrue(attachment)
                self.assertEqual(attachment.name, self.file.name)
                self.assertEqual(attachment.res_model, "account.move")
                self.assertEqual(attachment.res_id, invoice.id)
                self.assertEqual(attachment.mimetype, self.file.mimetype)
                self.assertEqual(
                    attachment.with_context(bin_size=False).datas,
                    self.file.with_context(bin_size=False).content,
                )

    def test_reuse_existing_invoice(self):
        self.action._execute_action(self.file)
        invoice = self.action.account_move_id
        attachment = invoice.message_main_attachment_id
        domain = [("res_model", "=", "account.move"), ("res_id", "=", invoice.id)]
        attachment_count = self.env["ir.attachment"].search_count(domain)
        invoice_count = self.env["account.move"].search_count([])
        result = self.action._execute_action(self.file)
        self.assertEqual(result["res_id"], invoice.id)
        self.assertEqual(self.action.account_move_id, invoice)
        self.assertEqual(invoice.message_main_attachment_id, attachment)
        self.assertEqual(self.env["account.move"].search_count([]), invoice_count)
        self.assertEqual(
            self.env["ir.attachment"].search_count(domain), attachment_count
        )

    def test_missing_journal(self):
        self.action.journal_id = False
        with self.assertRaisesRegex(ValueError, "Journal is not set"):
            self.action._execute_action(self.file)
        self.assertFalse(self.action.account_move_id)

    def test_create_invoice_without_partner(self):
        self.action.partner_id = False
        result = self.action._execute_action(self.file)
        invoice = self.action.account_move_id
        self.assertTrue(invoice)
        self.assertFalse(invoice.partner_id)
        self.assertEqual(invoice.state, "draft")
        self.assertEqual(result["res_id"], invoice.id)
