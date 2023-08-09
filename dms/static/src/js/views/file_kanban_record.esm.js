/** @odoo-module **/

import {CANCEL_GLOBAL_CLICK, KanbanRecord} from "@web/views/kanban/kanban_record";
import {useService} from "@web/core/utils/hooks";

export class FileKanbanRecord extends KanbanRecord {
    setup() {
        super.setup();
        this.messaging = useService("messaging");
        this.dialog = useService("dialog");
    }

    isPreviewCompatible(mimetype) {
        const ReaableMimetypes = [
            "image/bmp",
            "image/gif",
            "image/jpeg",
            "image/png",
            "image/svg+xml",
            "image/tiff",
            "image/x-icon",
            "application/pdf",
            "audio/mpeg",
            "video/x-matroska",
            "video/mp4",
            "video/webm",
        ];

        return ReaableMimetypes.includes(mimetype);
    }

    /**
     * @override
     *
     * Override to open the preview upon clicking the image, if compatible.
     */
    onGlobalClick(ev) {
        const self = this;

        if (!this.isPreviewCompatible(self.props.record.data.mimetype)) {
            return CANCEL_GLOBAL_CLICK;
        }

        if (ev.target.closest(".o_kanban_dms_file_preview")) {
            this.messaging.get().then((messaging) => {
                const attachmentList = messaging.models.AttachmentList.insert({
                    selectedAttachment: messaging.models.Attachment.insert({
                        id: self.props.record.data.id,
                        filename: self.props.record.data.name,
                        name: self.props.record.data.name,
                        mimetype: self.props.record.data.mimetype,
                        model_name: self.props.record.resModel,
                    }),
                });
                this.dialog = messaging.models.Dialog.insert({
                    attachmentListOwnerAsAttachmentView: attachmentList,
                });
            });
            return;
        }
        return super.onGlobalClick(...arguments);
    }
}
