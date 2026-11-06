// Copyright 2026 ledoent — Don Kendall
// License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

// Small wrappers around `window.localStorage` so the `try/catch` shape
// doesn't get repeated at every persistence site. LocalStorage throws
// in privacy mode and inside some sandboxed iframes — every read/write
// needs to fall back gracefully because losing a UI preference is OK
// but throwing inside a setup() hook crashes the component mount.

/**
 * Read a string from localStorage with a fallback.
 *
 * @param {String} key
 * @param {string|null} fallback - returned if the key is unset or storage throws
 * @returns {string|null}
 */
export function readStored(key, fallback = null) {
    try {
        const value = window.localStorage.getItem(key);
        return value === null ? fallback : value;
    } catch {
        return fallback;
    }
}

/**
 * Write a string to localStorage. Silent no-op on failure.
 *
 * @param {String} key
 * @param {String} value
 */
export function writeStored(key, value) {
    try {
        window.localStorage.setItem(key, value);
    } catch {
        // Persistence is best-effort.
    }
}
