/** @odoo-module **/

import {registerPatch} from "@mail/model/model_core";

registerPatch({
    name: "AttachmentBoxView",
    recordMethods: {
        _onAddDmsFile() {
            this.env.services.action.doAction(
                "dms_attachment_link.action_dms_file_wizard_selector_dms_attachment_link",
                {
                    additionalContext: {
                        active_id: this.chatter.thread.id,
                        active_ids: [this.chatter.thread.id],
                        active_model: this.chatter.threadModel,
                    },
                    onClose: this._onAddedDmsFile.bind(this),
                }
            );
        },
        _onAddedDmsFile() {
            this.chatter.refresh();
        },
    },
});

registerPatch({
    name: "Chatter",
    recordMethods: {
        /**
         * Handles click on the attach button.
         */
        async onClickButtonAddAttachments() {
            await this.onClickButtonToggleAttachments();
        },
    },
});
