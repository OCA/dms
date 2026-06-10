from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    show_original_dms_pages = fields.Boolean(
        string="Show Original File/Directories Page",
        config_parameter="dms_workspace_ui.show_original_dms_pages",
    )
    show_original_dms_field_documents_page = fields.Boolean(
        string="Show Original Documents Page",
        config_parameter="dms_workspace_ui.show_original_dms_field_documents_page",
    )
    bypass_delete_confirmation = fields.Boolean(
        string="Bypass delete confirmation",
        config_parameter="dms_workspace_ui.bypass_delete_confirmation",
    )

    @api.model
    def _dms_ui_param_enabled(self, name):
        value = self.env["ir.config_parameter"].sudo().get_param(name, "False")
        return str(value).lower() in {"1", "true", "yes", "on"}

    @api.model
    def _dms_ui_set_menu_visibility(self, xml_ids, visible):
        for xml_id in xml_ids:
            menu = self.env.ref(xml_id, raise_if_not_found=False)
            if menu:
                menu.sudo().write({"active": visible})

    @api.model
    def dms_ui_bypass_delete_confirmation(self):
        return self._dms_ui_param_enabled("dms_workspace_ui.bypass_delete_confirmation")

    @api.model
    def _dms_ui_apply_menu_visibility(self):
        self._dms_ui_set_menu_visibility(
            ["dms.menu_dms_file", "dms.menu_dms_directory"],
            self._dms_ui_param_enabled("dms_workspace_ui.show_original_dms_pages"),
        )
        self._dms_ui_set_menu_visibility(
            ["dms_field.dms_storage_menu"],
            self._dms_ui_param_enabled(
                "dms_workspace_ui.show_original_dms_field_documents_page"
            ),
        )

    def set_values(self):
        result = super().set_values()
        self._dms_ui_apply_menu_visibility()
        return result
