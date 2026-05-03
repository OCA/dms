# Copyright 2024 Subteno - Timothée Vannier (https://www.subteno.com).
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import api, models


class OnboardingOnboardingStep(models.Model):
    _inherit = "onboarding.onboarding.step"

    # ----------------------------------------------------------
    # Actions
    # ----------------------------------------------------------
    @api.model
    def action_open_documents_onboarding_storage(self):
        """
        Open the form to create a new storage from the onboarding panel.
        """
        return self.env.ref("dms.action_dms_storage_new").read()[0]

    @api.model
    def action_open_documents_onboarding_directory(self):
        """
        Open the form to create a new directory from the onboarding panel.
        """
        storage = self.env["dms.storage"].search([], order="create_date desc", limit=1)
        action = self.env.ref("dms.action_dms_directory_new").read()[0]
        action["context"] = {
            **self.env.context,
            **{
                "default_is_root_directory": True,
                "default_storage_id": storage and storage.id,
            },
        }
        return action

    @api.model
    def action_open_documents_onboarding_file(self):
        """
        Open the form to create a new file from the onboarding panel.
        """
        directory = self.env["dms.directory"].search(
            [], order="create_date desc", limit=1
        )
        action = self.env.ref("dms.action_dms_file_new").read()[0]
        action["context"] = {
            **self.env.context,
            **{"default_directory_id": directory and directory.id},
        }
        return action
