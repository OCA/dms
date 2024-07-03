# Copyright (C) 2024 Cetmix OÜ
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class Partner(models.Model):
    _inherit = "res.partner"

    dms_file_ids = fields.Many2many(
        comodel_name="dms.file",
        string="DMS Attachments",
        compute="_compute_dms_files",
    )
    dms_file_count = fields.Integer(compute="_compute_dms_files")

    @api.model
    def _get_partner_relations_in_models(self, models):
        """
        Finds all m2o fields with comodel 'res.partner' in
        a given list of models

        :param models: List of model names
        :type models: list[str]

        :return: Dictionary where key is model name
                and value is list of m2o field names
        """
        partner_relations = {}
        for model in models:
            fields = self.env[model]._fields
            partner_relations[model] = [
                field_name
                for field_name, field in fields.items()
                if field.type == "many2one" and field.comodel_name == "res.partner"
            ]
        return partner_relations

    @api.model
    def _map_partner_dms_files(self, files: list, relations: dict):
        """
        Map all found files to partner ids

        :param files: List of attachment files
        :type files: list[dict]
        :param relations: Dictionary where key is model name
                and value is list of m2o field names

        :return: Dictionary where key is partner id
                and value is list of file ids
        """
        partner_files = {}
        for file in files:
            if file["res_model"] == "res.partner":
                if file["res_id"] not in partner_files:
                    partner_files[file["res_id"]] = []
                partner_files[file["res_id"]].append(file["id"])

            elif file["res_model"] in relations:
                linked_record = self.env[file["res_model"]].browse(file["res_id"])
                for field_name in relations[file["res_model"]]:
                    partner_id = linked_record[field_name].id
                    if partner_id:
                        if partner_id not in partner_files:
                            partner_files[partner_id] = []
                        partner_files[partner_id].append(file["id"])

                    partner_id = file["res_id"]
                    if partner_id not in partner_files:
                        partner_files[partner_id] = []
                    partner_files[partner_id].append(file["id"])
        return partner_files

    def _compute_dms_files(self):
        """
        Compute DMS files
        related to these partners
        """
        dms_storage_obj = self.env["dms.storage"]
        attachment_storages = dms_storage_obj.search([("save_type", "=", "attachment")])
        attachment_files = attachment_storages.mapped("storage_file_ids").read(
            ["res_id", "res_model"]
        )
        partner_relations = self._get_partner_relations_in_models(
            list(set(map(lambda x: x["res_model"], attachment_files)))
        )
        partner_files = self._map_partner_dms_files(attachment_files, partner_relations)
        for partner in self:
            partner.dms_file_ids = self.env["dms.file"].browse(
                partner_files.get(partner.id, [])
            )
            partner.dms_file_count = len(partner.dms_file_ids)

    def action_open_dms_attachments(self):
        """
        Open action windows for DMS attachments
        related to this partner

        :return: Action Window
        :rtype: dict
        """
        self.ensure_one()
        action = self.env.ref("dms.action_dms_file").read()[0]
        action["domain"] = [
            ("id", "in", self.dms_file_ids.ids),
        ]
        return action
