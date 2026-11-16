/* Copyright 2024 Tecnativa - Carlos Roca
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl). */

// Material Symbols icon names (available in the web.icons_fonts subset)
const MAPPING = [
    ["image", /^image\//],
    ["audio_file", /^audio\//],
    ["video_file", /^video\//],
    ["picture_as_pdf", "application/pdf"],
    ["article", "text/plain"],
    ["code", ["text/html", "text/javascript", "application/javascript"]],
    [
        "folder_zip",
        [
            /^application\/x-(g?tar|xz|compress|bzip2|g?zip)$/,
            /^application\/x-(7z|rar|zip)-compressed$/,
            /^application\/(zip|gzip|tar)$/,
        ],
    ],
    [
        "description",
        [
            /ms-?word/,
            "application/vnd.oasis.opendocument.text",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ],
    ],
    [
        "slideshow",
        [
            /ms-?powerpoint/,
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ],
    ],
    [
        "table_chart",
        [
            /ms-?excel/,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ],
    ],
];
const DEFAULT_ICON = "description";

function match(mimetype, cond) {
    if (Array.isArray(cond)) {
        return cond.some((c) => match(mimetype, c));
    } else if (cond instanceof RegExp) {
        return cond.test(mimetype);
    }
    return mimetype === cond;
}

const cache = new Map();

/**
 * @param {String} mimetype
 * @returns {String} Material Symbols icon name, to be used as
 *  `<i class="oi" data-icon="..."/>`
 */
export function mimetype2icon(mimetype) {
    if (!mimetype) {
        return DEFAULT_ICON;
    }
    if (!cache.has(mimetype)) {
        const entry = MAPPING.find(([, cond]) => match(mimetype, cond));
        cache.set(mimetype, entry ? entry[0] : DEFAULT_ICON);
    }
    return cache.get(mimetype);
}
