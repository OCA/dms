# Copyright 2020 Creu Blanca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import _, fields, models

from odoo.addons.base.models.ir_ui_view import NameManager


class IrUiView(models.Model):

    _inherit = "ir.ui.view"

    type = fields.Selection(selection_add=[("dms_list", "DMS Tree")])

    def _postprocess_tag_dms_list(self, node, name_manager, node_info):
        parent = node.getparent()
        if parent_name := parent and parent.get("name"):
            field = name_manager.model._fields.get(parent_name)
            if field:
                model_name = field.comodel_name
                if model_name not in self.env:
                    self._raise_view_error(
                        _("Model not found: %(model)s", model=model_name), node
                    )
                model = self.env[model_name]
                new_name_manager = NameManager(model, parent=name_manager)
                root_info = {
                    "view_type": node.tag,
                    "view_editable": self._editable_node(node, name_manager),
                    "view_modifiers_from_model": self._modifiers_from_model(node),
                }
                new_node_info = dict(
                    root_info,
                    modifiers={},
                    editable=self._editable_node(node, new_name_manager),
                )
                for child in node:
                    self._postprocess_tag_field(child, new_name_manager, new_node_info)
