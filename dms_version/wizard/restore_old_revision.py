from odoo import api, fields, models


class RestoreOldRevision(models.TransientModel):
    _name = "restore.old.revision"
    _description = "Restore Old Revision"

    file_id = fields.Many2one(
        comodel_name="dms.file",
        required=True,
        string="Old Version",
    )
    current_revision_id = fields.Many2one(
        comodel_name="dms.file",
        string="Current Version",
        related="file_id.current_revision_id",
    )
    has_current_revision = fields.Boolean(
        related="file_id.has_current_revision",
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        active_id = self.env.context.get("active_id")
        res["file_id"] = (active_id,)
        return res

    def action_done(self):
        self.file_id.with_context(
            restore_old_revision=True
        ).action_restore_old_revision()
        return {"type": "ir.actions.act_window_close"}
