from odoo import api, fields, models


class DmsFile(models.Model):
    _inherit = "dms.file"

    description = fields.Text(
        help="Notes about the file, purpose, status, or review context.",
        tracking=True,
    )
    description_short = fields.Char(
        string="Short Description",
        compute="_compute_description_short",
        help="Short version of the description used on DMS kanban cards.",
    )

    @api.depends("description")
    def _compute_description_short(self):
        limit = 35
        for record in self:
            text = (
                (record.description or "").strip().replace("\r", " ").replace("\n", " ")
            )
            text = " ".join(text.split())
            if len(text) > limit:
                record.description_short = text[:limit].rstrip() + "..."
            else:
                record.description_short = text
