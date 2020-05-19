# Copyright 2020 Creu Blanca
# Copyright 2017-2019 MuK IT GmbH
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):

    _inherit = "res.company"

    # ----------------------------------------------------------
    # Database
    # ----------------------------------------------------------

    documents_onboarding_state = fields.Selection(
        selection=[
            ("not_done", "Not done"),
            ("just_done", "Just done"),
            ("done", "Done"),
            ("closed", "Closed"),
        ],
        string="Documents Onboarding State",
        default="not_done",
    )

    documents_onboarding_storage_state = fields.Selection(
        selection=[
            ("not_done", "Not done"),
            ("just_done", "Just done"),
            ("done", "Done"),
            ("closed", "Closed"),
        ],
        string="Documents Onboarding Storage State",
        default="not_done",
    )

    documents_onboarding_directory_state = fields.Selection(
        selection=[
            ("not_done", "Not done"),
            ("just_done", "Just done"),
            ("done", "Done"),
            ("closed", "Closed"),
        ],
        string="Documents Onboarding Directory State",
        default="not_done",
    )

    documents_onboarding_file_state = fields.Selection(
        selection=[
            ("not_done", "Not done"),
            ("just_done", "Just done"),
            ("done", "Done"),
            ("closed", "Closed"),
        ],
        string="Documents Onboarding File State",
        default="not_done",
    )

    # ----------------------------------------------------------
    # Functions
    # ----------------------------------------------------------

    def get_and_update_documents_onboarding_state(self):
        return self.get_and_update_onbarding_state(
            "documents_onboarding_state", self.get_documents_steps_states_names()
        )

    def get_documents_steps_states_names(self):
        return [
            "documents_onboarding_storage_state",
            "documents_onboarding_directory_state",
            "documents_onboarding_file_state",
        ]

    # ----------------------------------------------------------
    # Actions
    # ----------------------------------------------------------

    @api.model
    def action_open_documents_onboarding_storage(self):
        return self.env.ref("dms.action_dms_storage_new").read()[0]

    @api.model
    def action_open_documents_onboarding_directory(self):
        storage = self.env["dms.storage"].search([], order="create_date desc", limit=1)
        action = self.env.ref("dms.action_dms_directory_new").read()[0]
        action["context"] = {
            **self.env.context,
            **{
                "default_is_root_directory": True,
                "default_root_storage_id": storage and storage.id,
            },
        }
        return action

    @api.model
    def action_open_documents_onboarding_file(self):
        directory = self.env["dms.directory"].search(
            [], order="create_date desc", limit=1
        )
        action = self.env.ref("dms.action_dms_file_new").read()[0]
        action["context"] = {
            **self.env.context,
            **{"default_directory_id": directory and directory.id},
        }
        return action

    @api.model
    def action_close_documents_onboarding(self):
        self.env.user.company_id.documents_onboarding_state = "closed"
