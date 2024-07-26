/** @odoo-module **/

// /** ********************************************************************************
//     Copyright 2024 Subteno - Timothée Vannier (https://www.subteno.com).
//     License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
//  **********************************************************************************/
import {KanbanRecord} from "@web/views/kanban/kanban_record";
import {useFileViewer} from "@web/core/file_viewer/file_viewer_hook";
import {useService} from "@web/core/utils/hooks";

const videoReadableTypes = ["x-matroska", "mp4", "webm"];
const audioReadableTypes = ["mp3", "ogg", "wav", "aac", "mpa", "flac", "m4a"];

export class FileKanbanRecord extends KanbanRecord {
    setup() {
        super.setup();
        this.store = useService("mail.store");
        this.fileViewer = useFileViewer();
    }

    isVideo(mimetype) {
        return videoReadableTypes.includes(mimetype);
    }

    isAudio(mimetype) {
        return audioReadableTypes.includes(mimetype);
    }

    /**
     * @override
     *
     * Override to open the preview upon clicking the image, if compatible.
     */
    onGlobalClick(ev) {
        const self = this;

        if (ev.target.closest(".o_kanban_dms_file_preview")) {
            const file_type = self.props.record.data.name.split(".")[1];
            let mimetype = "";

            if (self.isVideo(file_type)) {
                mimetype = `video/${file_type}`;
            } else if (self.isAudio(file_type)) {
                mimetype = "audio/mpeg";
            } else {
                mimetype = self.props.record.data.mimetype;
            }

            const attachment = this.store.Attachment.insert({
                id: self.props.record.data.id,
                filename: self.props.record.data.name,
                name: self.props.record.data.name,
                mimetype: mimetype,
                model_name: self.props.record.resModel,
            });
            this.fileViewer.open(attachment);
            return;
        }
        return super.onGlobalClick(ev);
    }
}
