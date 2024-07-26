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
        };
    },
});
