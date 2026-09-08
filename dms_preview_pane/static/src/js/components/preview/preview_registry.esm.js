// Copyright 2026 ledoent — Don Kendall
// License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

// ===========================================================================
//  Extension point for DMS file preview handlers
// ===========================================================================
//
// The `dms` module ships in-browser preview handlers for the formats that
// every modern browser already understands: images, PDF, plain text +
// JSON/XML/JS, markdown, audio, video. Office formats
// (.doc/.docx/.odt/.xlsx/...) fall through to a download-only card because
// there is no in-browser viewer in base. Downstream modules plug in here
// to add native handlers — the first such is `dms_libreoffice_preview`
// (server-side soffice → PDF, score 10), and a future `dms_onlyoffice`
// would register at score 20 for live editing.
//
// ---------------------------------------------------------------------------
//  Contract
// ---------------------------------------------------------------------------
//
// A handler is a plain object registered against this category:
//
//     {
//         component: OwlComponent,    // receives {file: {id, name, mimetype,
//                                     //   write_date, human_size}} as a prop
//         match: (mimetype) => bool,  // OPTIONAL — predicate; if omitted,
//                                     //   the registry key is used as an
//                                     //   exact mimetype match
//         score: 10,                  // OPTIONAL — higher wins on ties;
//                                     //   built-ins use 0; download is -100
//     }
//
// Registering from an external module looks like this (verbatim from the
// real `dms_libreoffice_preview/static/src/js/libreoffice_preview.esm.js`):
//
//     import {registry} from "@web/core/registry";
//     import {LibreofficePreview} from "./libreoffice_preview.esm";
//
//     const OFFICE_MIMETYPES = new Set([
//         "application/msword",
//         "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
//         "application/vnd.oasis.opendocument.text",
//         "text/rtf",
//         // ... etc
//     ]);
//
//     registry.category("dms.preview_handlers").add("libreoffice", {
//         component: LibreofficePreview,
//         match: (mt) => OFFICE_MIMETYPES.has(mt),
//         score: 10,  // beats the built-in OfficeFallbackPreview card (score 0)
//     });
//
// The registered component must:
//   - declare `static template = "..."` and `static props = {file: Object}`
//   - render content that fits inside `.o_dms_preview_pane__body`
//     (no min-height required; the container handles overflow)
//
// ---------------------------------------------------------------------------
//  Lookup semantics
// ---------------------------------------------------------------------------
//
// `getPreviewHandler(mimetype)` returns the highest-scored handler whose
// `match` predicate accepts the mimetype (or whose registry key equals it,
// if no `match` is provided). The built-in `__download__` handler matches
// everything at score -100, so the function always returns something for any
// non-empty mimetype.

import {registry} from "@web/core/registry";

const CATEGORY = "dms.preview_handlers";

export function getPreviewHandler(mimetype) {
    if (!mimetype) {
        return null;
    }
    const handlers = registry.category(CATEGORY).getEntries();
    const matches = handlers
        .map(([key, h]) => ({key, ...h}))
        .filter((h) => {
            if (h.match) {
                return h.match(mimetype);
            }
            return h.key === mimetype;
        });
    if (!matches.length) {
        return null;
    }
    matches.sort((a, b) => (b.score || 0) - (a.score || 0));
    return matches[0];
}

export function previewRegistry() {
    return registry.category(CATEGORY);
}
