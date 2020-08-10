odoo.define("dms_field.field_utils", function(require) {
    "use strict";

    var utils = require("web.field_utils");

    function formatBinarySize(value, field, options) {
        var new_options = _.defaults(options || {}, {
            si: true,
        });
        var thresh = new_options.si ? 1000 : 1024;
        if (Math.abs(value) < thresh) {
            return utils.format.float(value, field, options) + " B";
        }
        var units = new_options.si
            ? ["KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
            : ["KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB"];
        var unit = -1;
        var new_value = value;
        do {
            new_value /= thresh;
            ++unit;
        } while (Math.abs(new_value) >= thresh && unit < units.length - 1);
        return utils.format.float(new_value, field, new_options) + " " + units[unit];
    }

    utils.format.binary_size = formatBinarySize;
});
