// Copyright 2026 ledoent — Don Kendall
// License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import {Component, useEffect, useState} from "@odoo/owl";
import {deserializeDateTime, formatDateTime} from "@web/core/l10n/dates";
import {readStored, writeStored} from "../../utils/storage.esm";
import {Chatter} from "@mail/chatter/web_portal/chatter";
import {getPreviewHandler} from "./preview_registry.esm";
import {useService} from "@web/core/utils/hooks";

const _CHATTER_VISIBLE_KEY = "dms_preview_chatter_visible";

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
    // Source-code extensions → dedicated code mimetypes that route to the
    // syntax-highlighting CodePreview (see _CODE_MIMETYPES in handlers).
    py: "text/x-python",
    js: "text/javascript",
    mjs: "text/javascript",
    cjs: "text/javascript",
    scss: "text/x-scss",
    css: "text/x-scss",
    sass: "text/x-scss",
    less: "text/x-scss",
    eml: "message/rfc822",
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
    const byExt = _EXTENSION_MIMETYPES[ext];
    // Generic stored type (libmagic couldn't tell) → trust the extension.
    if (!stored || _STORED_OVERRIDABLE.has(stored)) {
        return byExt || stored;
    }
    // Mis-typed media: an audio/video file occasionally carries an *image*
    // mimetype (a thumbnail type leaking onto it — the OCA dms demo stores
    // .wav as image/webp). An image type on a known audio/video extension is
    // effectively never right, so trust the extension. Content-detected types
    // are otherwise authoritative — a PDF mis-named ".mp4" still previews as
    // a PDF.
    if (
        byExt &&
        stored.startsWith("image/") &&
        ["audio", "video"].includes(byExt.split("/")[0])
    ) {
        return byExt;
    }
    return stored;
}

// Renders the currently-selected dms.file on the right of a split layout.
// Empty state when `recordId` is falsy; loads file metadata via ORM and
// dispatches to the registered handler for that mimetype.
export class FilePreviewPane extends Component {
    static template = "dms.FilePreviewPane";
    static components = {Chatter};
    static props = {
        recordId: {type: [Number, {value: null}], optional: true},
        // Bumped by the owning renderer when the on-screen record changes
        // out-of-band (e.g. inline rename) so the load effect re-fires even
        // though recordId is unchanged.
        reloadToken: {type: Number, optional: true},
        onClose: {type: Function, optional: true},
    };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            loading: false,
            file: null,
            error: null,
            // "preview" (the rendered file) | "details" (metadata + tags),
            // mirroring the Info & Tags pane of the first-party Documents app.
            tab: "preview",
            tags: [],
        });
        // When to (re)fetch: the recordId prop, plus reloadToken which the
        // renderer bumps when the on-screen record changed out-of-band (a
        // rename leaves recordId identical but the name stale). This is a
        // genuine side effect (an ORM read), so useEffect is the right tool.
        //
        // Owl-3 migration note: Owl 3 drops useEffect's dependency-array
        // second arg (deps auto-track) and the compat path is
        // useLayoutEffect — which Owl 2.8.2 (Odoo 19) does NOT export, so the
        // swap belongs at the master port, not here.
        useEffect(
            (recordId) => {
                if (recordId) {
                    this._load(recordId);
                } else {
                    this.state.file = null;
                    this.state.error = null;
                }
            },
            () => [this.props.recordId, this.props.reloadToken]
        );

        // Collapse state for the Activity tab's chatter — the pane owns its own
        // toggle (a plain `chatterState.isVisible` reactive + `onToggleChatter`,
        // animated in file_preview_pane.scss). Persisted per browser so a
        // collapsed chatter stays collapsed across navigation.
        const storedVisible = readStored(_CHATTER_VISIBLE_KEY);
        this.chatterState = useState({
            isVisible: storedVisible === null ? true : storedVisible === "1",
        });
        useEffect(
            () =>
                writeStored(
                    _CHATTER_VISIBLE_KEY,
                    this.chatterState.isVisible ? "1" : "0"
                ),
            () => [this.chatterState.isVisible]
        );
    }

    onToggleChatter() {
        this.chatterState.isVisible = !this.chatterState.isVisible;
    }

    async _load(recordId) {
        this.state.loading = true;
        this.state.error = null;
        try {
            const [file] = await this.orm.read(
                "dms.file",
                [recordId],
                [
                    "id",
                    "name",
                    "mimetype",
                    "extension",
                    "icon_url",
                    "write_date",
                    "create_date",
                    "human_size",
                    "create_uid",
                    "directory_id",
                    "path_names",
                    "tag_ids",
                ]
            );
            this.state.file = file || null;
            // Tag ids → names in a second read; cheap and only on (re)open.
            this.state.tags =
                file && file.tag_ids?.length
                    ? await this.orm.read("dms.tag", file.tag_ids, ["name"])
                    : [];
        } catch (err) {
            this.state.error = err.data?.message || err.message || String(err);
            this.state.file = null;
            this.state.tags = [];
        } finally {
            this.state.loading = false;
        }
    }

    setTab(tab) {
        this.state.tab = tab;
    }

    _fmtDate(value) {
        // Server UTC datetime string → user tz + locale display.
        return value ? formatDateTime(deserializeDateTime(value)) : "";
    }

    // Definition-list rows for the Details tab. m2o fields arrive as
    // [id, display_name]; path_names is the computed directory breadcrumb.
    get detailRows() {
        const f = this.state.file;
        if (!f) {
            return [];
        }
        return [
            {label: "Type", value: f.mimetype || f.extension || "—"},
            {label: "Size", value: f.human_size || "—"},
            {label: "Location", value: f.path_names || "—"},
            {label: "Owner", value: f.create_uid ? f.create_uid[1] : "—"},
            {label: "Created", value: this._fmtDate(f.create_date)},
            {label: "Modified", value: this._fmtDate(f.write_date)},
        ];
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
