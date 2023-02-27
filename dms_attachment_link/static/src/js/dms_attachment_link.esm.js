/** @odoo-module **/

import {AttachmentBox} from "@mail/components/attachment_box/attachment_box";
import {patch} from "web.utils";

patch(
    AttachmentBox.prototype,
    "dms_attachment_link/static/src/js/dms_attachment_link.js",
    {
        _onAddDmsFile() {
            this.env.bus.trigger("do-action", {
                action: "dms_attachment_link.action_dms_file_wizard_selector_dms_attachment_link",
                options: {
                    additional_context: {
                        active_id: this.messaging.models["mail.chatter"].get(
                            this.props.chatterLocalId
                        ).threadId,
                        active_ids: [
                            this.messaging.models["mail.chatter"].get(
                                this.props.chatterLocalId
                            ).threadId,
                        ],
                        active_model: this.messaging.models["mail.chatter"].get(
                            this.props.chatterLocalId
                        ).threadModel,
                    },
                    on_close: this._onAddedDmsFile.bind(this),
                },
            });
        },
        _onAddedDmsFile() {
            this.trigger("reload");
        },
    }
);
