# Copyright 2025 Kencove - Mohamed Alkobrosli (https://kencove.com).
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from lxml import etree

from odoo import api, fields, models


class RecordPlaceholder(models.TransientModel):
    _name = "record.placeholder"
    _description = "A placeholder model to enable virtual relational field res_id"


class WizardDmsDirRecord(models.TransientModel):
    _name = "wizard.directory.record"
    _description = "Wizard Dms Directory Record ID"

    directory_id = fields.Many2one(
        comodel_name="dms.directory",
        required=True,
        string="Directory",
        default=lambda self: self.env.context.get("directory_id_view_ref", False),
    )
    # Just a placeholder field
    res_id = fields.Many2one(
        "record.placeholder",
        string="Linked attachments record ID",
    )

    def validate(self):
        return True

    @api.model_create_multi
    def create(self, vals_list):
        dir_obj = self.env["dms.directory"]
        for vals in vals_list:
            res_id = vals.get("res_id")
            dir_id = dir_obj.browse(vals["directory_id"])
            # Todo as we can expand with more models for subscribtion like hr etc...
            if dir_id.res_model in ["res.partner"]:
                if dir_id.res_id and dir_id.res_id != res_id:
                    dir_id.message_unsubscribe([dir_id.res_id])
                subscribers = (
                    [res_id]
                    if res_id not in dir_id.sudo().message_partner_ids.ids
                    else None
                )
                dir_id.message_subscribe(subscribers)
            # Add the ID for the model
            dir_id.write({"res_id": res_id})
            # As the placeholder model is empty
            # we should remove its relational virtual field from creation.
            del vals["res_id"]
        return super().create(vals_list)

    @api.model
    def get_views(self, views, options=None):
        context = self.env.context
        res = super().get_views(views, options=options)
        if (
            "views" in res
            and "form" in res["views"]
            and context
            and context.get("directory_id_view_ref")
        ):
            dir_obj = self.env["dms.directory"]
            dir_id = dir_obj.browse(context.get("directory_id_view_ref"))
            model = dir_id.model_id
            relation = model.model
            res["models"][self._name]["fields"].update(
                {
                    "res_id": {
                        "string": "Linked attachments record ID",
                        "type": "many2one",
                        "relation": relation,
                        "required": True,
                    }
                }
            )
            eview = etree.fromstring(res["views"]["form"]["arch"])
            options = etree.Element("field", name="res_id")
            placeholder = eview.xpath("//separator[@string='options_placeholder']")[0]
            placeholder.getparent().replace(placeholder, options)
            res["views"]["form"]["arch"] = etree.tostring(eview, pretty_print=True)
        return res
