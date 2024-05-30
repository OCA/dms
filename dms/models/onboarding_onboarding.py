# Copyright 2024 Subteno - Timothée Vannier (https://www.subteno.com).
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import api, models


class OnboardingOnboarding(models.Model):
    _inherit = "onboarding.onboarding"

    # ----------------------------------------------------------
    # Actions
    # ----------------------------------------------------------
    @api.model
    def action_close_panel_dms_file(self):
        self.action_close_panel("dms.onboarding_onboarding_dms_file")
