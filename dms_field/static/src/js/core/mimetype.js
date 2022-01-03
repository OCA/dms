odoo.define("dms_field.mimetype", function () {
    "use strict";

    var mapping = [
        ["file-image-o", /^image\//],
        ["file-audio-o", /^audio\//],
        ["file-video-o", /^video\//],
        ["file-pdf-o", "application/pdf"],
        ["file-text-o", "text/plain"],
        ["file-code-o", ["text/html", "text/javascript", "application/javascript"]],
        [
            "file-archive-o",
            [
                /^application\/x-(g?tar|xz|compress|bzip2|g?zip)$/,
                /^application\/x-(7z|rar|zip)-compressed$/,
                /^application\/(zip|gzip|tar)$/,
            ],
        ],
        [
            "file-word-o",
            [
                /ms-?word/,
                "application/vnd.oasis.opendocument.text",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ],
        ],
        [
            "file-powerpoint-o",
            [
                /ms-?powerpoint/,
                "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ],
        ],
        [
            "file-excel-o",
            [
                /ms-?excel/,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ],
        ],
        ["file-o"],
    ];

    function match(mimetype, cond) {
        if (Array.isArray(cond)) {
            return cond.reduce(function (v, c) {
                return v || match(mimetype, c);
            }, false);
        } else if (cond instanceof RegExp) {
            return cond.test(mimetype);
        } else if (cond === undefined) {
            return true;
        }
        return mimetype === cond;
    }

    var cache = {};
    function resolve(mimetype) {
        if (cache[mimetype]) {
            return cache[mimetype];
        }
        for (var i = 0; i < mapping.length; i++) {
            if (match(mimetype, mapping[i][1])) {
                cache[mimetype] = mapping[i][0];
                return mapping[i][0];
            }
        }
    }

    function mimetype2fa(mimetype, options) {
        if (typeof mimetype === "object") {
            var new_options = mimetype;
            return function (new_mimetype) {
                return mimetype2fa(new_mimetype, new_options);
            };
        }
        var icon = resolve(mimetype);
        if (icon && options && options.prefix) {
            return options.prefix + icon;
        }
        return icon;
    }

    return {
        mimetype2fa: mimetype2fa,
    };
});
