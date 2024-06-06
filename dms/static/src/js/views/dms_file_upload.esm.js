/** @odoo-module */

import {useBus, useService} from "@web/core/utils/hooks";
import {_t} from "web.core";

const {useRef, useEffect, useState} = owl;

export const FileDropZone = {
    setup() {
        this._super();
        this.dragState = useState({
            showDragZone: false,
        });
        this.root = useRef("root");
        this.rpc = useService("rpc");

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
        await this.env.bus.trigger("change_file_input", {
            files: ev.dataTransfer.files,
        });
    },
};

export const FileUpload = {
    setup() {
        this._super();
        this.actionService = useService("action");
        this.notification = useService("notification");
        this.orm = useService("orm");
        this.http = useService("http");
        this.fileInput = useRef("fileInput");
        this.root = useRef("root");

        this.rpc = useService("rpc");

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

        this.onUpload(attachments);
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
        ctx.default_directory_id = false;
        if (this.props.domain) {
            for (const domain_item of this.props.domain) {
                if (domain_item.length === 3) {
                    if (domain_item[0] === "directory_id" && domain_item[1] === "=") {
                        ctx.default_directory_id = domain_item[2];
                    }
                }
            }
        }

        if (ctx.default_directory_id === false) {
            self.actionService.restore(controllerID);
            return self.notification.add(
                this.env._t("You must select a directory first"),
                {
                    type: "danger",
                }
            );
        }

        const attachment_datas = await this.orm.call(
            "dms.file",
            "get_dms_files_from_attachments",
            ["", attachmentIds]
        );

        const attachments_args = [];

        attachment_datas.forEach((attachment_data) => {
            attachments_args.push({
                name: attachment_data.name,
                content: attachment_data.datas,
                mimetype: attachment_data.mimetype,
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
