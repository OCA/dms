from odoo import Command
from odoo.tests import HttpCase, tagged

from odoo.addons.dms.tests.common import DocumentsBaseCase


@tagged("post_install", "-at_install")
class TestActionTour(HttpCase, DocumentsBaseCase):
    def _create_tour_file(self):
        storage = self.create_storage(save_type="database")
        directory = self.create_directory(storage=storage)
        file = self.create_file(directory=directory)
        server_action = self.env["ir.actions.server"].create(
            {
                "name": "Tour DMS server action",
                "model_id": self.env.ref("dms.model_dms_file").id,
                "state": "code",
                "code": "record.lock()",
            }
        )
        action = self.env["dms.action"].create(
            {
                "name": "Tour DMS action",
                "kind": "server_action",
                "action_id": server_action.id,
                "dms_directory_ids": [Command.link(directory.id)],
            }
        )
        group = self.env["res.groups"].create({"name": "Restricted tour group"})
        action.copy(
            {
                "name": "Forbidden DMS action",
                "group_ids": [Command.link(group.id)],
                "dms_directory_ids": [Command.link(directory.id)],
            }
        )
        return file

    def test_form_action_menu(self):
        file = self._create_tour_file()
        self.start_tour(
            f"/web#id={file.id}&model=dms.file&view_type=form",
            "dms_action_form_menu",
            login=self.dms_manager_user.login,
        )
        file.invalidate_recordset(["locked_by"])
        self.assertEqual(file.locked_by, self.dms_manager_user)

    def test_kanban_action_menu(self):
        file = self._create_tour_file()
        window_action = self.env["ir.actions.act_window"].create(
            {
                "name": "DMS action kanban tour",
                "res_model": "dms.file",
                "view_mode": "kanban,form",
                "view_id": self.env.ref("dms.view_dms_file_kanban").id,
                "domain": repr([("id", "=", file.id)]),
            }
        )
        self.start_tour(
            f"/web#action={window_action.id}",
            "dms_action_kanban_menu",
            login=self.dms_manager_user.login,
        )
        file.invalidate_recordset(["locked_by"])
        self.assertEqual(file.locked_by, self.dms_manager_user)
