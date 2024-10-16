from odoo.addons.base.tests.common import TransactionCase


class TestSaleDmsField(TransactionCase):
    def setUp(self):
        super(TestSaleDmsField, self).setUp()
        self.template = self.env.ref("sale_dms_field.field_template_sale")
        self.storage = self.template.storage_id
        self.access_group = self.template.group_ids
        self.sale_model = self.env["sale.order"]
        self.partner = self.env.ref("base.res_partner_12")
        self.test_directory = self.env["dms.directory"].create(
            {
                "name": "Test Directory",
                "parent_id": self.template.dms_directory_ids[0].id,
                "storage_id": self.template.storage_id.id,
            }
        )

    def test_01_sale_document_directory(self):
        sale_order = self.sale_model.create(
            {
                "partner_id": self.partner.id,
            }
        )
        sale_order.invalidate_model()
        directory = sale_order.dms_directory_ids
        # Assert that only one directory is created for the sale order.
        self.assertEqual(len(directory), 1, "Directory length must be 1.")
        # Assert that the storage associated with the directory is the same as the
        # template's storage.
        self.assertEqual(
            directory.storage_id,
            self.storage,
            "Sale order directory storage is different from the template storage.",
        )
        # Assert that the custom access group is present in the directory's group
        # list.
        self.assertIn(
            self.access_group,
            directory.group_ids,
            "Sale order directory groups are different from the template groups.",
        )
        # Map the names of child directories related to the sale order directory.
        child_directory_names = directory.mapped("child_directory_ids.name")
        # Assert that a specific child directory, "Test Directory", exists.
        self.assertIn(
            "Test Directory",
            child_directory_names,
            "Test Directory is not in the child directory of the sale order directory.",
        )
