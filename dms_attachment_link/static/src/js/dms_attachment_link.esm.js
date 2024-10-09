/** @odoo-module **/

import {Chatter} from "@mail/core/web/chatter";
import {patch} from "@web/core/utils/patch";

patch(Chatter.prototype, {
    _onAddDmsFile() {
        this.action.doAction(
            "dms_attachment_link.action_dms_file_wizard_selector_dms_attachment_link",
            {
                additionalContext: {
                    active_id: this.state.thread.id,
                    active_ids: [this.state.thread.id],
                    active_model: this.state.thread.model,
                },
                onClose: async () => {
                    await this._onAddedDmsFile();
                },
            }
        );
    },
    onClickAddAttachments(ev) {
        ev.stopPropagation();
        this.state.isAttachmentBoxOpened = !this.state.isAttachmentBoxOpened;
        if (this.state.isAttachmentBoxOpened) {
            this.rootRef.el.scrollTop = 0;
            this.state.thread.scrollTop = "bottom";
        }
    },
    async _onAddedDmsFile() {
        this.reloadParentView();
    },
});
