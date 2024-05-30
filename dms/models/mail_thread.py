# Copyright 2021 Tecnativa - Jairo Llopis
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import models


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    def _process_attachments_for_post(self, attachments, attachment_ids, message_data):
        """Indicate to DMS that we're attaching a message to a record."""
        _self = self.with_context(attaching_to_record=True)
        return super(MailThread, _self)._process_attachments_for_post(
            attachments, attachment_ids, message_data
        )
