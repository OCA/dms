/** @odoo-module **/

import {_t} from "@web/core/l10n/translation";
import {localDateTimeLabel} from "@dms_workspace_ui/js/dms_ui_core.esm";

export function itemKey(item) {
    return `${item.type}_${item.id}`;
}

export function dmsUiDirectorySection(env) {
    const categories = env?.searchModel?.categories || [];
    return categories.find((section) => section.fieldName === "directory_id");
}

export function directoryFromSearchPanelValue(value) {
    return {
        type: "directory",
        id: value.id,
        name: value.display_name,
        parentId: value.parentId || false,
        active: !value.dms_ui_archived,
        fileCount: value.__count || 0,
        permissions: value.dms_ui_permissions || {},
    };
}

export function parentDirectoryItem(parentValue = false) {
    const targetName = parentValue?.display_name || _t("All Documents");
    return {
        ...(parentValue
            ? directoryFromSearchPanelValue(parentValue)
            : {
                  type: "directory",
                  id: false,
                  name: targetName,
                  parentId: false,
                  active: true,
                  fileCount: 0,
                  permissions: {},
              }),
        type: "parent-directory",
        key: "parent_directory",
        name: "..",
        targetName,
    };
}

function directoryCountLabel(count = 0, singularLabel, pluralLabel) {
    const value = count || 0;
    return value === 1 ? _t(singularLabel) : _t(pluralLabel, {count: value});
}

export function directoryFileCountLabel(count = 0) {
    return directoryCountLabel(count, "1 file", "%(count)s files");
}

export function directoryFolderCountLabel(count = 0) {
    return directoryCountLabel(count, "1 folder", "%(count)s folders");
}

export function normalizeDirectoryItem(directory) {
    return {
        ...directory,
        key: itemKey(directory),
        active: directory.active !== false,
        writeDate: localDateTimeLabel(directory.writeDate),
    };
}
