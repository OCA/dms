/** @odoo-module */

// /** ********************************************************************************
//     Copyright 2024 Subteno - Timothée Vannier (https://www.subteno.com).
//     License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
//  **********************************************************************************/

import {useBus, useService} from "@web/core/utils/hooks";
import {_t} from "@web/core/l10n/translation";

const {useRef, useEffect, useState} = owl;

export function createFileDropZoneExtension() {
    return {
        setup() {
            super.setup(...arguments);
            this.dragState = useState({
                showDragZone: false,
            });
            this.root = useRef("root");

            useEffect(
                (el) => {
                    if (!el) {
                        return;
                    }
                    const highlight = this.highlight.bind(this);
                    const unhighlight = this.unhighlight.bind(this);
                    const drop = this.onDrop.bind(this);
                    el.addEventListener("dragover", highlight);
                    el.addEventListener("dragleave", unhighlight);
                    el.addEventListener("drop", drop);
                    return () => {
                        el.removeEventListener("dragover", highlight);
                        el.removeEventListener("dragleave", unhighlight);
                        el.removeEventListener("drop", drop);
                    };
                },

                () => [document.querySelector(".o_content")]
            );
        },

        highlight(ev) {
            ev.stopPropagation();
            ev.preventDefault();
            this.dragState.showDragZone = true;
        },

        unhighlight(ev) {
            ev.stopPropagation();
            ev.preventDefault();
            this.dragState.showDragZone = false;
        },

        async onDrop(ev) {
            ev.preventDefault();
            this.dragState.showDragZone = false;
            await this.env.bus.trigger("change_file_input", {
                files: ev.dataTransfer.files,
            });
        },
    };
}

export function createFileUploadExtension() {
    return {
        setup() {
            super.setup();
            this.notification = useService("notification");
            this.orm = useService("orm");
            this.http = useService("http");
            this.fileInput = useRef("fileInput");

            useBus(this.env.bus, "change_file_input", async (ev) => {
                this.fileInput.el.files = ev.detail.files;
                await this.onChangeFileInput();
            });
        },

        uploadDocument() {
            this.fileInput.el.click();
        },

        async onChangeFileInput() {
            const params = {
                csrf_token: odoo.csrf_token,
                ufile: [...this.fileInput.el.files],
                model: "dms.file",
                id: 0,
            };

            const fileData = await this.http.post(
                "/web/binary/upload_attachment",
                params,
                "text"
            );
            const attachments = JSON.parse(fileData);
            if (attachments.error) {
                throw new Error(attachments.error);
            }

            await this.onUpload(attachments);
        },

        async onUpload(attachments) {
            const self = this;
            const attachmentIds = attachments.map((a) => a.id);
            const ctx = this.props.context;
            const controllerID = this.actionService.currentController.jsId;

            if (!attachmentIds.length) {
                this.notification.add(_t("An error occurred during the upload"));
                return;
            }

            // Search the correct directory_id value according to the domain
            let directory_id = false;
            if (this.props.domain) {
                for (const domain_item of this.props.domain) {
                    if (domain_item.length === 3) {
                        if (
                            domain_item[0] === "directory_id" &&
                            ["=", "child_of"].includes(domain_item[1])
                        ) {
                            directory_id = domain_item[2];
                        }
                    }
                }
            }

            if (directory_id === false) {
                self.actionService.restore(controllerID);
                return self.notification.add(_t("You must select a directory first"), {
                    type: "danger",
                });
            }

            const attachment_datas = await this.orm.call(
                "dms.file",
                "get_dms_files_from_attachments",
                [],
                {attachment_ids: attachmentIds}
            );

            const attachments_args = [];

            attachment_datas.forEach((attachment_data) => {
                attachments_args.push({
                    name: attachment_data.name,
                    content: attachment_data.datas,
                    mimetype: attachment_data.mimetype,
                    directory_id,
                });
            });

            this.orm
                .call("dms.file", "create", [attachments_args], {
                    context: ctx,
                })
                .then(() => {
                    self.actionService.restore(controllerID);
                })
                .catch((error) => {
                    self.notification.add(error.data.message, {
                        type: "danger",
                    });
                    self.actionService.restore(controllerID);
                });
        },
    };
}
