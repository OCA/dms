/** @odoo-module **/

// /** ********************************************************************************
//     Copyright 2024 Subteno - Timothée Vannier (https://www.subteno.com).
//     License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
//  **********************************************************************************/
import {LinkPreview} from "@mail/core/common/link_preview";
import {patch} from "@web/core/utils/patch";

patch(LinkPreview, {
    get imageUrl() {
        return function compute() {
            if (!this.attachment) {
                return;
            }
            if (
                !this.attachment.accessToken &&
                this.attachment.originThread &&
                this.attachment.originThread.model === "mail.channel"
            ) {
                return `/mail/channel/${this.attachment.originThread.id}/image/${this.attachment.id}/${this.width}x${this.height}`;
            }
            const accessToken = this.attachment.accessToken
                ? `?access_token=${this.attachment.accessToken}`
                : "";
            if (
                this.attachment.model_name &&
                this.attachment.model_name === "dms.file"
            ) {
                return `/web/content?id=${this.attachment.id}&field=content&model=dms.file&filename_field=name&download=false`;
            }
            return `/web/image/${this.attachment.id}/${this.width}x${this.height}${accessToken}`;
        };
    },
});
