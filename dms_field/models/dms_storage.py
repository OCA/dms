# Copyright 2020 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, models
from odoo.exceptions import ValidationError


class DmsStorage(models.Model):

    _inherit = "dms.storage"

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
        return [record._build_documents_storage(record) for record in self.search([])]

    @api.constrains("model_ids", "save_type")
    def _constrain_model_ids(self):
        for storage in self:
            if storage.save_type == "attachment":
                continue
            if self.env["dms.directory"].search(
                [
                    ("root_storage_id", "=", storage.id),
                    ("is_root_directory", "=", True),
                    ("res_model", "not in", storage.mapped("model_ids.model"),),
                ]
            ):
                raise ValidationError(
                    _("Some directories are inconsistent with the storage models")
                )
            if storage.model_ids and self.env["dms.directory"].search(
                [
                    ("root_storage_id", "=", storage.id),
                    ("is_root_directory", "=", True),
                    ("res_model", "=", False),
                ]
            ):
                raise ValidationError(
                    _("There are directories not associated to a record")
                )
