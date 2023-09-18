/** @odoo-module **/

import {registerPatch} from "@mail/model/model_core";
import {attr} from "@mail/model/model_field";

registerPatch({
    name: "Attachment",
    fields: {
        defaultSource: {
            compute() {
                if (this.isImage) {
                    if (this.model_name && this.model_name === "dms.file") {
                        return `/web/content?id=${this.id}&field=content&model=dms.file&filename_field=name&download=false`;
                    }
                    return `/web/image/${this.id}?signature=${this.checksum}`;
                }
                if (this.isPdf) {
                    if (this.model_name && this.model_name === "dms.file") {
                        return (
                            "/web/content?id=" +
                            this.id +
                            "&field=content&model=dms.file" +
                            "&filename_field=name"
                        );
                    }
                    const pdf_lib = `/web/static/lib/pdfjs/web/viewer.html?file=`;
                    if (
                        !this.accessToken &&
                        this.originThread &&
                        this.originThread.model === "mail.channel"
                    ) {
                        return `${pdf_lib}/mail/channel/${this.originThread.id}/attachment/${this.id}#pagemode=none`;
                    }
                    const accessToken = this.accessToken
                        ? `?access_token%3D${this.accessToken}`
                        : "";
                    return `${pdf_lib}/web/content/${this.id}${accessToken}#pagemode=none`;
                }
                if (this.isUrlYoutube) {
                    const urlArr = this.url.split("/");
                    let token = urlArr[urlArr.length - 1];
                    if (token.includes("watch")) {
                        token = token.split("v=")[1];
                        const amp = token.indexOf("&");
                        if (amp !== -1) {
                            token = token.substring(0, amp);
                        }
                    }
                    return `https://www.youtube.com/embed/${token}`;
                }
                if (
                    !this.accessToken &&
                    this.originThread &&
                    this.originThread.model === "mail.channel"
                ) {
                    return `/mail/channel/${this.originThread.id}/attachment/${this.id}`;
                }
                const accessToken = this.accessToken
                    ? `?access_token=${this.accessToken}`
                    : "";

                if (this.model_name && this.model_name === "dms.file") {
                    return `/web/content?id=${this.id}&field=content&model=dms.file&filename_field=name`;
                }
                return `/web/content/${this.id}${accessToken}`;
            },
        },
        model_name: attr(),
        downloadUrl: {
            compute() {
                if (
                    !this.accessToken &&
                    this.originThread &&
                    this.originThread.model === "mail.channel"
                ) {
                    return `/mail/channel/${this.originThread.id}/attachment/${this.id}?download=true`;
                }
                if (this.model_name && this.model_name === "dms.file") {
                    return `/web/content?id=${this.id}&field=content&model=dms.file&filename_field=name&download=true`;
                }
                const accessToken = this.accessToken
                    ? `access_token=${this.accessToken}&`
                    : "";
                return `/web/content/ir.attachment/${this.id}/datas?${accessToken}download=true`;
            },
        },
    },
});
