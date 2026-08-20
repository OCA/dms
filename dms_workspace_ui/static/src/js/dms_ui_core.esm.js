/** @odoo-module **/

import {browser} from "@web/core/browser/browser";
import {cookie} from "@web/core/browser/cookie";
import {_t} from "@web/core/l10n/translation";
import {user} from "@web/core/user";

export const TREE_STATE_KEY = `dms_workspace_ui.expanded.${user.userId || "anonymous"}`;
export const TREE_WIDTH_KEY = `dms_workspace_ui.tree_width.${user.userId || "anonymous"}`;
export const INSPECTOR_WIDTH_KEY = `dms_workspace_ui.inspector_width.${user.userId || "anonymous"}`;
export const WORKSPACE_SELECTOR = ".dms_ui_workspace";
export const TREE_HEADER_SELECTOR = ".o_search_panel .dms_ui_directory_header";
export const TREE_WIDTH_MIN = 160;
export const TREE_WIDTH_MAX = 520;
export const INSPECTOR_BREADCRUMB_MAX_LINES = 3;
const DMS_UI_COLOR_SCHEMES = [
    "purple",
    "teal",
    "charcoal",
    "blue",
    "green",
    "red",
    "cyan",
    "amber",
];

function dmsUiNormalizeColorScheme(scheme) {
    const normalizedScheme =
        typeof scheme === "string" ? scheme.toLowerCase().trim() : scheme;
    return DMS_UI_COLOR_SCHEMES.includes(normalizedScheme)
        ? normalizedScheme
        : "purple";
}

export function dmsUiColorScheme() {
    return dmsUiNormalizeColorScheme(cookie.get("dms_ui_color_scheme"));
}

export function dmsUiColorMode() {
    const scheme = cookie.get("color_scheme");
    if (scheme === "dark" || scheme === "light") {
        return scheme;
    }
    return window.matchMedia?.("(prefers-color-scheme: dark)")?.matches
        ? "dark"
        : "light";
}

export function clampNumber(value, min, max) {
    return Math.max(min, Math.min(max, value));
}

export function rowsForRenderedItems(items) {
    const renderedItems = items
        .filter(Boolean)
        .sort((a, b) => a.rect.top - b.rect.top || a.rect.left - b.rect.left);
    const rows = [];
    for (const item of renderedItems) {
        const row = rows[rows.length - 1];
        if (!row || Math.abs(row.top - item.rect.top) > 4) {
            rows.push({top: item.rect.top, items: [item]});
        } else {
            row.items.push(item);
        }
    }
    for (const row of rows) {
        row.items.sort((a, b) => a.rect.left - b.rect.left);
    }
    return rows;
}

export function storedWidth(key, fallback, min, max) {
    const value = Number(browser.localStorage.getItem(key));
    return Number.isFinite(value) && value > 0
        ? clampNumber(value, min, max)
        : fallback;
}

export function rememberWidth(key, value, min, max) {
    browser.localStorage.setItem(key, String(Math.round(clampNumber(value, min, max))));
}

function recordValue(record, fieldName, fallback = false) {
    return fieldName in record.data ? record.data[fieldName] : fallback;
}

function relationDisplayName(value) {
    if (!value) {
        return "";
    }
    if (Array.isArray(value)) {
        return value[1] || "";
    }
    if (typeof value === "object") {
        return value.display_name || value.name || "";
    }
    return String(value);
}

function relationId(value) {
    if (!value) {
        return false;
    }
    if (Array.isArray(value)) {
        return value[0] || false;
    }
    if (typeof value === "object") {
        return value.id || false;
    }
    return false;
}

export function localDateTimeLabel(dateValue) {
    if (!dateValue) {
        return "-";
    }
    const value = String(dateValue).trim();
    if (!value) {
        return "-";
    }
    const noSubseconds = value.replace(/\.\d+/, "");
    const normalized = noSubseconds.includes(" ")
        ? noSubseconds.replace(" ", "T")
        : noSubseconds;
    let parsed = new Date(normalized);
    if (Number.isNaN(parsed.getTime())) {
        parsed = new Date(normalized.replace(/([+-]\d{2})(\d{2})$/, "$1:$2"));
    }
    if (Number.isNaN(parsed.getTime())) {
        return value;
    }
    const month = String(parsed.getMonth() + 1).padStart(2, "0");
    const day = String(parsed.getDate()).padStart(2, "0");
    const year = String(parsed.getFullYear());
    const hours = parsed.getHours();
    const hour = String(hours % 12 || 12);
    const minute = String(parsed.getMinutes()).padStart(2, "0");
    const meridian = hours >= 12 ? "PM" : "AM";
    return `${month}-${day}-${year} ${hour}:${minute} ${meridian}`;
}

export function isBrowserPreviewableFile(file) {
    return (
        ["application/pdf", "text/plain"].includes(file.mimetype) ||
        ["audio/", "image/", "video/"].some((prefix) =>
            file.mimetype.startsWith(prefix)
        )
    );
}

export function normalizeFileRecord(record) {
    const file = {
        type: "file",
        id: record.resId,
        localId: record.id,
        name: recordValue(record, "name", ""),
        color: recordValue(record, "color", 0),
        active: recordValue(record, "active", true),
        mimetype: recordValue(record, "mimetype", ""),
        humanSize: recordValue(record, "human_size", ""),
        directoryId: relationId(recordValue(record, "directory_id", false)),
        location: relationDisplayName(recordValue(record, "directory_id", false)),
        writeDate: localDateTimeLabel(recordValue(record, "write_date", false)),
        onlyofficeCanOpen: recordValue(record, "onlyoffice_can_open", false),
    };
    return {...file, previewable: isBrowserPreviewableFile(file)};
}

export function fileUrl(file, downloadFile = false) {
    return (
        `/web/content?id=${file.id}&field=content&model=dms.file` +
        `&filename_field=name&download=${downloadFile ? "true" : "false"}`
    );
}

export function fileAttachment(store, file) {
    return store.Attachment.insert({
        id: file.id,
        filename: file.name,
        name: file.name,
        mimetype: file.mimetype,
        model_name: "dms.file",
    });
}

export function errorMessage(error) {
    return (
        error.data?.message ||
        error.message ||
        _t("The operation could not be completed.")
    );
}

export function refsForFiles(files) {
    return files.map((file) => ({type: "file", id: file.id}));
}

export function refsForItems(items) {
    return items.map((item) => ({type: item.type, id: item.id}));
}

export function selectedFileIds(target) {
    const items = target.items?.length
        ? target.items
        : [{type: target.type, id: target.id}];
    return [
        ...new Set(items.filter((item) => item.type === "file").map((item) => item.id)),
    ];
}

export function selectedDirectoryIds(target) {
    const items = target.items?.length
        ? target.items
        : [{type: target.type, id: target.id}];
    return [
        ...new Set(
            items.filter((item) => item.type === "directory").map((item) => item.id)
        ),
    ];
}

export function recordsForList(list) {
    if (list.records) {
        return list.records;
    }
    return (list.groups || []).flatMap((group) => recordsForList(group.list));
}

export function isSpaceKey(event) {
    return event.code === "Space" || event.key === " " || event.key === "Spacebar";
}

export function isEnterKey(event) {
    return (
        event.key === "Enter" || event.code === "Enter" || event.code === "NumpadEnter"
    );
}

export function isTextEntryTarget(target) {
    return (
        target?.isContentEditable ||
        Boolean(target?.closest?.("input, select, textarea"))
    );
}

export function isTypeaheadKey(event) {
    return (
        !event.ctrlKey &&
        !event.altKey &&
        !event.metaKey &&
        event.key.length === 1 &&
        !isSpaceKey(event)
    );
}

export function updateTypeahead(buffer, key) {
    const now = Date.now();
    const previous = now - buffer.updatedAt < 800 ? buffer.query : "";
    const query = `${previous}${key}`.toLocaleLowerCase();
    buffer.query = query;
    buffer.updatedAt = now;
    return query;
}

export function stopEvent(event) {
    event.preventDefault();
    event.stopPropagation();
    event.stopImmediatePropagation?.();
}

export function isWorkspaceMounted() {
    return Boolean(document.querySelector(WORKSPACE_SELECTOR));
}

export function isWorkspaceEventTarget(target) {
    return Boolean(target?.closest?.(`${WORKSPACE_SELECTOR}, .o_search_panel`));
}

export function isSearchViewTarget(target) {
    return Boolean(target?.closest?.(".o_searchview"));
}

export function focusSearchViewInput() {
    requestAnimationFrame(() => {
        const input = document.querySelector(
            ".o_control_panel .o_searchview_input, " +
                ".o_control_panel .o_searchview input, " +
                ".o_searchview .o_searchview_input, " +
                ".o_searchview input"
        );
        input?.focus({preventScroll: true});
    });
}

export function focusDirectoryTree() {
    requestAnimationFrame(() => {
        const active = document.querySelector(`${TREE_HEADER_SELECTOR}.active`);
        const first = document.querySelector(TREE_HEADER_SELECTOR);
        (active || first)?.focus();
    });
}

export function focusFirstFilePaneItem() {
    const focusItem = () => {
        const element = document.querySelector(
            `${WORKSPACE_SELECTOR} .dms_ui_custom_item:not(.dms_ui_parent_directory), ` +
                `${WORKSPACE_SELECTOR} .o_kanban_record, ` +
                `${WORKSPACE_SELECTOR} tr.o_data_row .o_data_cell, ` +
                `${WORKSPACE_SELECTOR} tr.o_data_row, ` +
                `${WORKSPACE_SELECTOR} .dms_ui_custom_item.dms_ui_parent_directory`
        );
        element?.focus({preventScroll: true});
        return Boolean(element);
    };
    const focusContainer = () => {
        const container = document.querySelector(
            `${WORKSPACE_SELECTOR} .dms_ui_custom_browser`
        );
        container?.focus({preventScroll: true});
    };
    requestAnimationFrame(() => {
        if (focusItem()) {
            return;
        }
        requestAnimationFrame(() => {
            if (focusItem()) {
                return;
            }
            window.setTimeout(() => {
                if (!focusItem()) {
                    focusContainer();
                }
            }, 40);
        });
    });
}

export function focusTokenForDirectory(directory) {
    return directory?.id
        ? {type: "tree-directory", id: directory.id}
        : {type: "tree-all"};
}

export function focusTokenForContentItem(item) {
    if (!item) {
        return {type: "content-root"};
    }
    if (item.type === "file") {
        return {type: "file", id: item.id, localId: item.localId};
    }
    if (item.type === "directory") {
        return {type: "content-directory", id: item.id};
    }
    if (item.type === "parent-directory") {
        return {type: "parent-directory"};
    }
    return {type: "content-root"};
}

function focusFileTokenNow(token) {
    const selector = token.localId
        ? `${WORKSPACE_SELECTOR} .o_kanban_record[data-id="${token.localId}"], ` +
          `${WORKSPACE_SELECTOR} tr.o_data_row[data-id="${token.localId}"], ` +
          `${WORKSPACE_SELECTOR} .dms_ui_custom_item[data-local-id="${token.localId}"]`
        : "";
    const targetElement =
        (selector && document.querySelector(selector)) ||
        document.querySelector(
            `${WORKSPACE_SELECTOR} .dms_ui_custom_item[data-item-key="file_${token.id}"]`
        ) ||
        document.querySelector(
            `${WORKSPACE_SELECTOR} .o_kanban_record.dms_ui_selected_record, ` +
                `${WORKSPACE_SELECTOR} tr.o_data_row.dms_ui_selected_record, ` +
                `${WORKSPACE_SELECTOR} .dms_ui_custom_item.dms_ui_selected_record, ` +
                `${WORKSPACE_SELECTOR} .o_kanban_record:focus, ` +
                `${WORKSPACE_SELECTOR} tr.o_data_row:focus-within, ` +
                `${WORKSPACE_SELECTOR} .dms_ui_custom_item:focus`
        );
    if (targetElement?.matches("tr")) {
        (targetElement.querySelector(".o_data_cell") || targetElement).focus();
    } else {
        targetElement?.focus();
    }
    return Boolean(targetElement);
}

function focusTreeDirectoryTokenNow(token) {
    const header = document.querySelector(
        `${TREE_HEADER_SELECTOR}[data-directory-id="${token.id}"]`
    );
    header?.focus();
    return Boolean(header);
}

function focusTreeAllTokenNow() {
    const headers = [...document.querySelectorAll(TREE_HEADER_SELECTOR)].filter(
        (header) => header.offsetParent
    );
    const allHeader =
        headers.find((header) => !Number(header.dataset.directoryId || 0)) ||
        headers[0];
    allHeader?.focus();
    return Boolean(allHeader);
}

function focusContentDirectoryTokenNow(token) {
    const element = document.querySelector(
        `${WORKSPACE_SELECTOR} .dms_ui_custom_item[data-item-key="directory_${token.id}"]`
    );
    element?.focus({preventScroll: true});
    return Boolean(element);
}

function focusParentDirectoryTokenNow() {
    const element = document.querySelector(
        `${WORKSPACE_SELECTOR} .dms_ui_custom_item.dms_ui_parent_directory`
    );
    element?.focus({preventScroll: true});
    return Boolean(element);
}

function focusContentRootTokenNow() {
    const element = document.querySelector(
        `${WORKSPACE_SELECTOR} .dms_ui_custom_browser`
    );
    element?.focus({preventScroll: true});
    return Boolean(element);
}

export function focusWorkspaceTokenNow(token) {
    const focusToken = token?.focusToken || token;
    if (!focusToken) {
        return false;
    }
    if (focusToken.type === "file") {
        return focusFileTokenNow(focusToken);
    }
    if (focusToken.type === "content-directory") {
        return focusContentDirectoryTokenNow(focusToken);
    }
    if (focusToken.type === "parent-directory") {
        return focusParentDirectoryTokenNow();
    }
    if (focusToken.type === "content-root" || focusToken.type === "empty") {
        return focusContentRootTokenNow();
    }
    if (focusToken.type === "tree-directory" || focusToken.type === "directory") {
        return focusTreeDirectoryTokenNow(focusToken);
    }
    if (focusToken.type === "tree-all") {
        return focusTreeAllTokenNow();
    }
    return false;
}

export function focusWorkspaceTokenSoon(token) {
    if (!token) {
        return;
    }
    requestAnimationFrame(() => focusWorkspaceTokenNow(token));
    for (const delay of [40, 120, 300, 600]) {
        window.setTimeout(() => focusWorkspaceTokenNow(token), delay);
    }
}

export function focusContextTargetNow(target) {
    focusWorkspaceTokenNow(target);
}

export function focusContextTargetSoon(target) {
    focusWorkspaceTokenSoon(target);
    requestAnimationFrame(() => focusWorkspaceTokenSoon(target));
}

export function onceCallback(callback) {
    let called = false;
    return (...args) => {
        if (called) {
            return;
        }
        called = true;
        return callback(...args);
    };
}

function focusDialogSelector(selector) {
    for (const delay of [0, 60, 180]) {
        window.setTimeout(() => {
            const element = document.querySelector(selector);
            element?.focus();
            element?.select?.();
        }, delay);
    }
}

export function focusDeleteConfirmButton() {
    focusDialogSelector(
        ".modal.show .modal-footer .btn-danger, " +
            ".modal.show .modal-footer .btn-primary, " +
            ".o_dialog .modal-footer .btn-danger, " +
            ".o_dialog .modal-footer .btn-primary"
    );
}

export function focusFileViewer() {
    for (const delay of [0, 60, 180]) {
        window.setTimeout(() => {
            document.querySelector(".o-FileViewer")?.focus({preventScroll: true});
        }, delay);
    }
}

export function forceFocusInputRef(ref, {select = false} = {}) {
    const focus = () => {
        const input = ref.el;
        if (!input) {
            return;
        }
        input.focus({preventScroll: true});
        if (select) {
            input.select();
        }
    };
    focus();
    requestAnimationFrame(focus);
    for (const delay of [60, 180, 400]) {
        window.setTimeout(focus, delay);
    }
}
