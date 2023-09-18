/** @odoo-module **/

import {registerPatch} from "@mail/model/model_core";

registerPatch({
    name: "AttachmentViewerViewable",
    fields: {
        imageUrl: {
            compute() {
                if (
                    !this.attachmentOwner.accessToken &&
                    this.attachmentOwner.originThread &&
                    this.attachmentOwner.originThread.model === "mail.channel"
                ) {
                    return `/mail/channel/${this.attachmentOwner.originThread.id}/image/${this.attachmentOwner.id}`;
                }
                const accessToken = this.attachmentOwner.accessToken
                    ? `?access_token=${this.attachmentOwner.accessToken}`
                    : "";
                if (
                    this.attachmentOwner.model_name &&
                    this.attachmentOwner.model_name === "dms.file"
                ) {
                    return `/web/content?id=${this.attachmentOwner.id}&field=content&model=dms.file&filename_field=name&download=false`;
                }
                return `/web/image/${this.attachmentOwner.id}${accessToken}`;
            },
        },
    },
});
