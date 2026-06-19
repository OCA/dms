// /** ********************************************************************************
//     Copyright 2026 ledoent — Don Kendall
//     License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
//
//     Plugs an "office mimetypes → server-converted PDF" handler into the
//     existing dms.preview_handlers registry. Score 10 beats the score-0
//     OfficeFallbackPreview (download card) shipped in base dms, while
//     leaving room for a future dms_onlyoffice handler at score 20 to win
//     when in-browser editing is the goal.
//
//     The component reuses the existing PdfPreview iframe class
//     (`o_dms_preview__iframe`) so no new SCSS is needed — once the server
//     emits the converted PDF, the browser's native PDF viewer handles
//     rendering exactly as it does for source-PDF files today.
//  **********************************************************************************/
import {Component} from "@odoo/owl";
import {previewRegistry} from "@dms_preview_pane/js/components/preview/preview_registry.esm";

// Must stay in lockstep with OFFICE_MIMETYPES in
// dms_libreoffice_preview/models/dms_file.py — the JS predicate gates UI
// display, the Python set gates server-side conversion. Drift between
// them produces a clickable office card with a 404 preview.
const OFFICE_MIMETYPES = new Set([
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.oasis.opendocument.text",
    "application/rtf",
    "text/rtf",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.oasis.opendocument.spreadsheet",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.oasis.opendocument.presentation",
]);

export class LibreofficePreview extends Component {
    static template = "dms_libreoffice_preview.Preview";
    static props = {file: {type: Object}};

    get src() {
        // Write_date doubles as the cache-bust query param so the iframe
        // refetches whenever the source file changes. Server caches on the
        // same write_date so two requests for the same generation hit the
        // attachment store, not soffice.
        const ts = encodeURIComponent(this.props.file.write_date || "");
        return `/dms/file/${this.props.file.id}/libreoffice_preview?v=${ts}`;
    }
}

previewRegistry().add("dms_libreoffice_preview/office", {
    component: LibreofficePreview,
    match: (mt) => OFFICE_MIMETYPES.has(mt),
    score: 10,
});
