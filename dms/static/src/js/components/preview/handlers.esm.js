// Copyright 2026 ledoent — Don Kendall
// License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import {Component, onWillStart, useState} from "@odoo/owl";
import {previewRegistry} from "./preview_registry.esm";

// ---------------------------------------------------------------------------
// Built-in preview handlers
//
// Each handler is a tiny OWL component receiving a `file` prop:
//     {id, name, mimetype, write_date}
// Handlers render a fixed-height container (CSS handles sizing) and either
// embed the file or expose a click-out affordance.
// ---------------------------------------------------------------------------

const fileProps = {file: {type: Object}};
const downloadUrl = (file) =>
    `/web/content?id=${file.id}&amp;model=dms.file&amp;field=content` +
    `&amp;filename_field=name&amp;download=true`;

// Image preview: native <img> at /web/image/<id>/image_1920.
export class ImagePreview extends Component {
    static template = "dms.preview.Image";
    static props = fileProps;

    get src() {
        return `/web/image/dms.file/${this.props.file.id}/image_1920`;
    }
}

// PDF: native <iframe> using browser PDF viewer; works for all modern browsers.
export class PdfPreview extends Component {
    static template = "dms.preview.Pdf";
    static props = fileProps;

    get src() {
        // Append timestamp to bust cache when the file is updated.
        const ts = encodeURIComponent(this.props.file.write_date || "");
        return (
            `/web/content?id=${this.props.file.id}&model=dms.file` +
            `&field=content&filename_field=name&v=${ts}`
        );
    }
}

// Plain text / source files: native <iframe> serving the raw bytes via
// `/web/content`. The browser renders `text/plain` (and the application/*
// mimetypes browsers also display as text — json, xml) directly with its
// built-in source view. No fetch + <pre> approach is needed; offloading to
// the browser keeps the handler tiny and inherits scrollbars, find-in-page,
// and selection for free. Mirrors the PdfPreview shape exactly.
export class TextPreview extends Component {
    static template = "dms.preview.Text";
    static props = fileProps;

    get src() {
        const ts = encodeURIComponent(this.props.file.write_date || "");
        return (
            `/web/content?id=${this.props.file.id}&model=dms.file` +
            `&field=content&filename_field=name&v=${ts}`
        );
    }
}

// Markdown: client-side render to HTML, displayed in a sandboxed iframe
// via srcdoc. The sandbox attribute denies scripts and top navigation so
// untrusted markdown can't execute as XSS. The render covers the common
// GFM subset (headings, bold/italic, inline + fenced code, links, lists)
// — anything outside that shows up as escaped text, which is acceptable
// "view content" semantics for a preview pane.
function _renderMarkdown(src) {
    // Escape HTML first so author-provided <script>...</script> never runs.
    let html = src.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    // Fenced code blocks BEFORE other rules (their content shouldn't get
    // re-interpreted as markdown).
    html = html.replace(
        /```([\s\S]+?)```/g,
        (_, code) => "<pre><code>" + code.trim() + "</code></pre>"
    );
    // Headings (h1..h3 cover ~all real-world DMS markdown).
    html = html.replace(/^### (.+)$/gm, "<h3>$1</h3>");
    html = html.replace(/^## (.+)$/gm, "<h2>$1</h2>");
    html = html.replace(/^# (.+)$/gm, "<h1>$1</h1>");
    // Inline formatting.
    html = html.replace(/\*\*([^*\n]+)\*\*/g, "<strong>$1</strong>");
    html = html.replace(/(^|[^*])\*([^*\n]+)\*/g, "$1<em>$2</em>");
    html = html.replace(/`([^`\n]+)`/g, "<code>$1</code>");
    // Links: [text](url) — only http/https/mailto allowed to defend against
    // javascript:-URL injection.
    html = html.replace(
        /\[([^\]]+)\]\((https?:\/\/[^)]+|mailto:[^)]+)\)/g,
        '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>'
    );
    // Unordered lists — group adjacent <li> rows under one <ul>.
    html = html.replace(/^- (.+)$/gm, "<li>$1</li>");
    html = html.replace(/(?:<li>.*<\/li>\n?)+/g, (m) => "<ul>" + m + "</ul>");
    // Paragraph wrap on blank-line splits; leave block elements alone.
    return html
        .split(/\n{2,}/)
        .map((block) => {
            if (/^<(h[123]|ul|pre|p)/.test(block.trimStart())) {
                return block;
            }
            return "<p>" + block.replace(/\n/g, "<br>") + "</p>";
        })
        .join("\n");
}

export class MarkdownPreview extends Component {
    static template = "dms.preview.Markdown";
    static props = fileProps;

    setup() {
        this.state = useState({html: "", error: null});
        onWillStart(async () => {
            try {
                const r = await fetch(this._sourceUrl);
                if (!r.ok) {
                    throw new Error("HTTP " + r.status);
                }
                this.state.html = _renderMarkdown(await r.text());
            } catch (e) {
                this.state.error = String(e.message || e);
            }
        });
    }

    get _sourceUrl() {
        const ts = encodeURIComponent(this.props.file.write_date || "");
        return (
            `/web/content?id=${this.props.file.id}&model=dms.file` +
            `&field=content&filename_field=name&v=${ts}`
        );
    }

    get srcdoc() {
        const body = this.state.error
            ? `<p style="color:#dc3545">Failed to load: ${this.state.error}</p>`
            : this.state.html;
        return (
            "<!doctype html><html><head><meta charset='utf-8'><style>" +
            "body{font-family:system-ui,sans-serif;padding:16px 24px;" +
            "max-width:80ch;color:#212529;line-height:1.5}" +
            "h1,h2,h3{margin-top:1.2em;color:#1a1a1a}" +
            "h1{font-size:1.6em;border-bottom:1px solid #e5e5e5;padding-bottom:.3em}" +
            "h2{font-size:1.3em}h3{font-size:1.1em}" +
            "pre{background:#f4f5f7;padding:12px 14px;border-radius:4px;" +
            "overflow:auto;font-size:.85em}" +
            "code{background:#f4f5f7;padding:2px 5px;border-radius:3px;" +
            "font-size:.9em;font-family:ui-monospace,Menlo,monospace}" +
            "pre code{background:transparent;padding:0}" +
            "a{color:#714b67}ul{padding-left:22px}p{margin:.6em 0}" +
            "</style></head><body>" +
            body +
            "</body></html>"
        );
    }
}

// Audio: HTML5 <audio>.
export class AudioPreview extends Component {
    static template = "dms.preview.Audio";
    static props = fileProps;

    get src() {
        return (
            `/web/content?id=${this.props.file.id}&model=dms.file` +
            `&field=content&filename_field=name`
        );
    }
}

// Video: HTML5 <video>.
export class VideoPreview extends Component {
    static template = "dms.preview.Video";
    static props = fileProps;

    get src() {
        return (
            `/web/content?id=${this.props.file.id}&model=dms.file` +
            `&field=content&filename_field=name`
        );
    }
}

// Office formats: no in-browser viewer in base; fall back to a download
// card with a pointer to the modules that DO provide one. A future
// `dms_libreoffice_preview` (server-side soffice → PDF) would let the
// existing PdfPreview handler take over transparently; `dms_onlyoffice`
// would register a higher-score handler that embeds the editor.
export class OfficeFallbackPreview extends Component {
    static template = "dms.preview.OfficeFallback";
    static props = fileProps;

    get downloadHref() {
        return downloadUrl(this.props.file);
    }
}

// Generic fallback: Download-only card. Always wins LAST (score=-100).
export class DownloadFallbackPreview extends Component {
    static template = "dms.preview.DownloadFallback";
    static props = fileProps;

    get downloadHref() {
        return downloadUrl(this.props.file);
    }
}

// ---------------------------------------------------------------------------
// Registration
// ---------------------------------------------------------------------------
const reg = previewRegistry();

reg.add("image/*", {
    component: ImagePreview,
    match: (mt) => mt.startsWith("image/"),
    score: 0,
});
reg.add("application/pdf", {component: PdfPreview, score: 0});
reg.add("text/*", {
    component: TextPreview,
    match: (mt) =>
        mt.startsWith("text/") ||
        mt === "application/json" ||
        mt === "application/xml" ||
        mt === "application/javascript",
    score: 0,
});
// Markdown rendering wins over the generic text/* handler (score 0) so
// `text/markdown` files render as formatted HTML instead of raw source.
reg.add("text/markdown", {
    component: MarkdownPreview,
    match: (mt) => mt === "text/markdown",
    score: 5,
});
reg.add("audio/*", {
    component: AudioPreview,
    match: (mt) => mt.startsWith("audio/"),
    score: 0,
});
reg.add("video/*", {
    component: VideoPreview,
    match: (mt) => mt.startsWith("video/"),
    score: 0,
});

const OFFICE_MIMETYPES = new Set([
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.oasis.opendocument.text",
    "application/rtf",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.oasis.opendocument.spreadsheet",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.oasis.opendocument.presentation",
]);

reg.add("office/*", {
    component: OfficeFallbackPreview,
    match: (mt) => OFFICE_MIMETYPES.has(mt),
    score: 0,
});

reg.add("__download__", {
    component: DownloadFallbackPreview,
    match: () => true,
    score: -100,
});
