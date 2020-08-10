# Copyright 2020 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class DmsStorage(models.Model):

    _inherit = "dms.storage"

    model_id = fields.Many2one("ir.model", auto_join=True)

    @api.model
    def _build_documents_storage(self, storage):
        storage_directories = []
        model = self.env["dms.directory"]
        directories = model.search_parents([["storage_id", "=", storage.id]])
        for record in directories:
            storage_directories.append(model._build_documents_view_directory(record))
        return {
            "id": "storage_%s" % storage.id,
            "text": storage.name,
            "icon": "fa fa-database",
            "type": "storage",
            "data": {"odoo_id": storage.id, "odoo_model": "dms.storage"},
            "children": storage_directories,
        }

    @api.model
    def get_js_tree_data(self):
        initial_data = []
        for record in self.search([]):
            initial_data.append(record._build_documents_storage(record))
        return initial_data
