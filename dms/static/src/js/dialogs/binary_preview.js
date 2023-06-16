/** @odoo-module **/

import {Dialog} from "@web/core/dialog/dialog";

const {Component} = owl;


export class BinaryPreviewDialog extends Component {
    setup() {
        super.setup();
    }
}

BinaryPreviewDialog.template = "dms.BinaryPreviewDialog"
BinaryPreviewDialog.components = {Dialog}
BinaryPreviewDialog.props = {
    title: String,
    url: String,
    type: String,
    isImage: false,
    isVideo: false,
    close: Function
};
