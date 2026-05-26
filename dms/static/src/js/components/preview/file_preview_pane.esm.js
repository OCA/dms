// Copyright 2026 ledoent — Don Kendall
// License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import {Component, useEffect, useState} from "@odoo/owl";
import {getPreviewHandler} from "./preview_registry.esm";
import {useService} from "@web/core/utils/hooks";

// Filename extension → mimetype fallback for `_effectiveMimetype`. libmagic
// returns `application/octet-stream` for several common file types whose
// magic bytes vary across encoders (notably MP4 container variants) — the
// pane would then route to DownloadFallbackPreview even though VideoPreview
// or similar would handle the file fine. Mapping by extension fixes this
// without forcing every uploader to set mimetype manually.
const _EXTENSION_MIMETYPES = {
    mp4: "video/mp4",
    webm: "video/webm",
    mkv: "video/x-matroska",
    mov: "video/quicktime",
    mp3: "audio/mpeg",
    ogg: "audio/ogg",
    wav: "audio/wav",
    m4a: "audio/mp4",
    flac: "audio/flac",
    pdf: "application/pdf",
    md: "text/markdown",
    markdown: "text/markdown",
    txt: "text/plain",
    json: "application/json",
    xml: "application/xml",
    js: "application/javascript",
    rtf: "text/rtf",
    csv: "text/csv",
    html: "text/html",
    htm: "text/html",
    png: "image/png",
    jpg: "image/jpeg",
    jpeg: "image/jpeg",
    gif: "image/gif",
    webp: "image/webp",
    svg: "image/svg+xml",
};

// Mimetypes generic enough that an extension-derived mapping should win.
// libmagic returns `text/plain` for .md/.markdown/.json/.xml/.csv (no magic
// signature distinguishes them from prose), so the registry would route
// those to TextPreview instead of MarkdownPreview / JSON / etc.
const _STORED_OVERRIDABLE = new Set([
    "application/octet-stream",
    "application/x-binary",
    "text/plain",
]);

function _effectiveMimetype(file) {
    const stored = file.mimetype || "";
    const ext = (file.name || "").split(".").pop().toLowerCase();
    if (stored && !_STORED_OVERRIDABLE.has(stored)) {
        return stored;
    }
    return _EXTENSION_MIMETYPES[ext] || stored;
}

// Renders the currently-selected dms.file on the right of a split layout.
// Empty state when `recordId` is falsy; loads file metadata via ORM and
// dispatches to the registered handler for that mimetype.
export class FilePreviewPane extends Component {
    static template = "dms.FilePreviewPane";
    static props = {
        recordId: {type: [Number, {value: null}], optional: true},
        onClose: {type: Function, optional: true},
    };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            loading: false,
            file: null,
            error: null,
        });
        // Single source of truth for "when to (re)fetch": the recordId prop.
        // `useEffect` fires on initial mount AND every time the dependency
        // changes, replacing the prior setup()-conditional + onWillUpdateProps
        // pair with one declarative wiring. Returns undefined (no teardown)
        // because the fetch result lives on this.state which the component
        // re-render handles.
        useEffect(
            (recordId) => {
                if (recordId) {
                    this._load(recordId);
                } else {
                    this.state.file = null;
                    this.state.error = null;
                }
            },
            () => [this.props.recordId]
        );
    }

    async _load(recordId) {
        this.state.loading = true;
        this.state.error = null;
        try {
            const [file] = await this.orm.read(
                "dms.file",
                [recordId],
                ["id", "name", "mimetype", "write_date", "human_size"]
            );
            this.state.file = file || null;
        } catch (err) {
            this.state.error = err.data?.message || err.message || String(err);
            this.state.file = null;
        } finally {
            this.state.loading = false;
        }
    }

    get handler() {
        if (!this.state.file) {
            return null;
        }
        return getPreviewHandler(_effectiveMimetype(this.state.file));
    }

    get HandlerComponent() {
        return this.handler?.component || null;
    }

    onCloseClick() {
        if (this.props.onClose) {
            this.props.onClose();
        }
    }

    async onOpenFormClick() {
        if (!this.state.file) {
            return;
        }
        // Resolve the addon's registered action so we land in the same
        // context the user clicked into (breadcrumbs, search context, etc).
        // Plain `{type: "ir.actions.act_window", res_model, res_id}` was
        // losing the action context and redirecting to the apps menu.
        await this.action.doAction("dms.action_dms_file", {
            viewType: "form",
            additionalContext: {},
            props: {resId: this.state.file.id},
        });
    }

    onDownloadClick() {
        if (!this.state.file) {
            return;
        }
        // Direct content endpoint — `download=true` sends the right Content-
        // Disposition header; the browser handles save-as without leaving
        // the pane. New tab keeps the kanban/list selection intact.
        const url =
            `/web/content?model=dms.file&id=${this.state.file.id}` +
            `&field=content&filename_field=name&download=true`;
        window.open(url, "_blank", "noopener");
    }

    async onShareClick() {
        if (!this.state.file) {
            return;
        }
        // The existing dms `wizard_dms_file_share_action` is a binding-model
        // action — its underlying `wizard.dms.share` (inherits portal.share)
        // reads `active_model` + `active_ids` from context to seed the
        // wizard's res_model + res_id fields.
        await this.action.doAction("dms.wizard_dms_file_share_action", {
            additionalContext: {
                active_id: this.state.file.id,
                active_ids: [this.state.file.id],
                active_model: "dms.file",
            },
        });
    }
}
