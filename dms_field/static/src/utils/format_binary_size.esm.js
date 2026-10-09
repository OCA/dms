import {formatFloat} from "@web/views/fields/formatters";

export function formatBinarySize(value) {
    var thresh = 1000;
    if (Math.abs(value) < thresh) {
        return formatFloat(value) + " B";
    }
    var units = ["KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"];
    var unit = -1;
    var new_value = value;
    do {
        new_value /= thresh;
        ++unit;
    } while (Math.abs(new_value) >= thresh && unit < units.length - 1);
    return formatFloat(new_value) + " " + units[unit];
}
