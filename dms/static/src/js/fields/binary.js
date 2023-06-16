/** @odoo-module **/

import {BinaryField} from "@web/views/fields/binary/binary_field";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";
import {BinaryPreviewDialog} from "../dialogs/binary_preview";

export class PreviewBinaryField extends BinaryField {
    setup() {
        super.setup()
        this.dialogService = useService("dialog")
    }

    preview(ev) {
        ev.preventDefault()
        const attachmentUrl = this._getContentUrl(this.props.record)
        const type = this.props.record.data.mimetype.split('/')[0]
        const props = {
            title: this.props.record.data.name,
            url: attachmentUrl,
            type: this.props.record.data.mimetype,
            isImage: type === 'image',
            isVideo: type === 'video',
        }
        console.log(this.props.record)
        this.dialogService.add(BinaryPreviewDialog, props)
    }


    _getContentUrl(attachment) {
        return (
            "/web/content/" +
            attachment.resModel +
            "/" +
            attachment.data.id +
            "/content" +
            "?filename=" +
            window.encodeURIComponent(attachment.data.name)
        );
    }
}


PreviewBinaryField.template = 'dms.PreviewBinaryField'
registry.category('fields').add('preview_binary', PreviewBinaryField)
