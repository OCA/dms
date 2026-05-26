// Copyright 2026 ledoent — Don Kendall
// License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import {useEffect, useState} from "@odoo/owl";
import {readStored, writeStored} from "./storage.esm";

// `useStoredState(key, default, {serializer, deserializer})`
//
// useState that auto-loads from localStorage on setup and persists every
// change via useEffect. The returned reactive can be templated as-is —
// `state.value` for reads, `state.value = x` for writes. Persistence is
// best-effort (writeStored swallows quota / privacy-mode failures).
//
// Sibling addons should import this rather than re-implementing the
// readStored/writeStored ceremony in every component. See PATTERNS.md
// (cross-cutting design tokens) for the rationale.
//
// @example
//   this.density = useStoredState("dms_kanban_density", "comfortable");
//   // template: t-att-data-density="density.value"
//   this.density.value = "compact"; // persists "compact"
//
//   this.open = useStoredState("dms_kanban_pane_open", true, {
//       serializer: (v) => (v ? "1" : "0"),
//       deserializer: (v) => v === "1",
//   });
export function useStoredState(key, defaultValue, options = {}) {
    const {serializer = String, deserializer = (v) => v} = options;
    const raw = readStored(key);
    const initial = raw !== null ? deserializer(raw) : defaultValue;
    const state = useState({value: initial});
    useEffect(
        () => writeStored(key, serializer(state.value)),
        () => [state.value]
    );
    return state;
}

// `useDmsPreviewState(storageKey)`
//
// Shared side-pane state for the file kanban + list renderers. Encapsulates:
//   - `open` (boolean, persisted) — user's hide/show choice
//   - `recordId` (number|null, NOT persisted — it's tied to the current view)
//   - `toggle()` — flips open and clears recordId on hide
//   - `close()` — full dismissal (Esc + header X)
//   - `select(resId)` — row/card click; opens pane and sets the record
//
// Returns one object so consumers can do `this.preview = useDmsPreviewState(...)`
// and templates read `preview.open` / `preview.recordId` directly.
export function useDmsPreviewState(storageKey) {
    const openState = useStoredState(storageKey, true, {
        serializer: (v) => (v ? "1" : "0"),
        deserializer: (v) => v === "1",
    });
    const idState = useState({value: null});

    return {
        get open() {
            return openState.value;
        },
        get recordId() {
            return idState.value;
        },
        toggle() {
            openState.value = !openState.value;
            if (!openState.value) {
                idState.value = null;
            }
        },
        close() {
            openState.value = false;
            idState.value = null;
        },
        select(resId) {
            if (!resId) {
                return;
            }
            openState.value = true;
            idState.value = resId;
        },
    };
}
