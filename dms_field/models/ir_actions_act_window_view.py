# Copyright 2020 Creu Blanca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class IrActionsActWindowView(models.Model):

    _inherit = "ir.actions.act_window.view"

    view_mode = fields.Selection(
        selection_add=[("dms_tree", "DMS Tree")], ondelete={"dms_tree": "cascade"}
    )
