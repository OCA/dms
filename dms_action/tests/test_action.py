# Copyright 2022 CreuBlanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.dms.tests.common import DocumentsBaseCase


class TestAction(DocumentsBaseCase):
    def setUp(self):
        super().setUp()
        self.server_action = self.env["ir.actions.server"].create(
            {
                "name": "server action",
                "model_id": self.env.ref("dms.model_dms_file").id,
                "state": "code",
                "code": "record.lock()",
            }
        )
        self.storage = self.create_storage(save_type="database")
        self.directory = self.create_directory(storage=self.storage)
        self.action = self.env["dms.action"].create(
            {
                "name": "Action",
                "kind": "server_action",
                "action_id": self.server_action.id,
                "dms_directory_ids": self.directory,
            }
        )
        self.file = self.create_file(directory=self.directory)

    def test_action(self):
        self.assertFalse(self.file.locked_by)
        self.file.execute_action(kwargs={"action_id": self.action.id})
        self.assertTrue(self.file.locked_by)
