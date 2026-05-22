// /** ********************************************************************************
//     Copyright 2026 ledoent — Don Kendall
//     License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
//
//     Locks down the side-pane state machine on both the file kanban + list
//     renderers. Routing a card/row click into the renderer's preview state
//     is the single regression-prone seam between Phase 3 (registry) and
//     Phase 11 (side-pane). These pure-state tests catch logic-only bugs;
//     a separate mount-view test covers t-att-data-preview-open serialization
//     (Phase 12c later).
//  **********************************************************************************/

import {beforeEach, describe, expect, test} from "@odoo/hoot";
import {FileKanbanRenderer} from "@dms/js/views/file_kanban_renderer.esm";
import {FileListRenderer} from "@dms/js/views/file_list_renderer.esm";

const PREVIEW_KEY_LIST = "dms_list_preview_pane";
const PREVIEW_KEY_KANBAN = "dms_kanban_preview_pane";

function _clearStorage() {
    try {
        window.localStorage.removeItem(PREVIEW_KEY_LIST);
        window.localStorage.removeItem(PREVIEW_KEY_KANBAN);
    } catch {
        // Best-effort.
    }
}

function _kanban() {
    const inst = Object.create(FileKanbanRenderer.prototype);
    inst.previewState = {open: true, recordId: null};
    return inst;
}

function _list() {
    const inst = Object.create(FileListRenderer.prototype);
    inst.previewState = {open: true, recordId: null};
    return inst;
}

beforeEach(() => _clearStorage());

describe("FileKanbanRenderer.selectForPreview", () => {
    test("sets recordId + opens pane + persists open=1", () => {
        const inst = _kanban();
        inst.previewState.open = false; // Start closed
        inst.selectForPreview(42);
        expect(inst.previewState.open).toBe(true);
        expect(inst.previewState.recordId).toBe(42);
        expect(window.localStorage.getItem(PREVIEW_KEY_KANBAN)).toBe("1");
    });

    test("ignores falsy resId (defensive — kanban records may render before resId resolves)", () => {
        const inst = _kanban();
        inst.previewState.open = false;
        inst.selectForPreview(null);
        inst.selectForPreview(undefined);
        inst.selectForPreview(0);
        expect(inst.previewState.recordId).toBe(null);
        expect(inst.previewState.open).toBe(false);
    });

    test("togglePreview flips open + clears recordId when closing", () => {
        const inst = _kanban();
        inst.previewState.recordId = 7;
        inst.togglePreview();
        expect(inst.previewState.open).toBe(false);
        expect(inst.previewState.recordId).toBe(null);
        expect(window.localStorage.getItem(PREVIEW_KEY_KANBAN)).toBe("0");
    });

    test("closePreview fully dismisses the pane + persists open=0", () => {
        // The pane header's X button and the Esc key both route here.
        // Users expect a full dismissal; the pane going from "file
        // selected" → "empty state but still visible" reads as a broken
        // close affordance. Persist so the choice survives navigation.
        const inst = _kanban();
        inst.previewState.open = true;
        inst.previewState.recordId = 9;
        inst.closePreview();
        expect(inst.previewState.open).toBe(false);
        expect(inst.previewState.recordId).toBe(null);
        expect(window.localStorage.getItem(PREVIEW_KEY_KANBAN)).toBe("0");
    });
});

describe("FileListRenderer.onCellClicked", () => {
    test("sets recordId + persists open=1 + stops event propagation", () => {
        const inst = _list();
        inst.previewState.open = false;
        const events = {stopped: false, prevented: false};
        const ev = {
            stopPropagation: () => (events.stopped = true),
            preventDefault: () => (events.prevented = true),
        };
        inst.onCellClicked({resId: 33}, null, ev);
        expect(inst.previewState.open).toBe(true);
        expect(inst.previewState.recordId).toBe(33);
        expect(events.stopped).toBe(true);
        expect(events.prevented).toBe(true);
        expect(window.localStorage.getItem(PREVIEW_KEY_LIST)).toBe("1");
    });

    test("ignores record without resId (defensive — new unsaved rows)", () => {
        const inst = _list();
        inst.previewState.open = false;
        // Mock super.onCellClicked via the prototype chain.
        let superCalled = false;
        const origProto = Object.getPrototypeOf(FileListRenderer.prototype);
        const originalSuper = origProto.onCellClicked;
        origProto.onCellClicked = function () {
            superCalled = true;
        };
        try {
            inst.onCellClicked({resId: null}, null, {});
            expect(inst.previewState.recordId).toBe(null);
            expect(superCalled).toBe(true);
        } finally {
            origProto.onCellClicked = originalSuper;
        }
    });
});

describe("FileListRenderer.getRowClass", () => {
    test("appends accent class when row is the selected preview record", () => {
        const inst = _list();
        inst.previewState.recordId = 99;
        // Mock super.getRowClass to return a fixed base value so we test our
        // appending behavior, not the parent's logic.
        const origProto = Object.getPrototypeOf(FileListRenderer.prototype);
        const originalSuper = origProto.getRowClass;
        origProto.getRowClass = function () {
            return "o_data_row";
        };
        try {
            const cls = inst.getRowClass({resId: 99});
            expect(cls).toContain("o_data_row");
            expect(cls).toContain("o_dms_preview_selected_row");
        } finally {
            origProto.getRowClass = originalSuper;
        }
    });

    test("does NOT append accent class for non-selected rows", () => {
        const inst = _list();
        inst.previewState.recordId = 99;
        const origProto = Object.getPrototypeOf(FileListRenderer.prototype);
        const originalSuper = origProto.getRowClass;
        origProto.getRowClass = function () {
            return "o_data_row";
        };
        try {
            const cls = inst.getRowClass({resId: 42});
            expect(cls).toContain("o_data_row");
            expect(cls.includes("o_dms_preview_selected_row")).toBe(false);
        } finally {
            origProto.getRowClass = originalSuper;
        }
    });
});

describe("FileListRenderer.isPreviewSelected", () => {
    test("true when recordId matches the row's resId", () => {
        const inst = _list();
        inst.previewState.recordId = 12;
        expect(inst.isPreviewSelected({resId: 12})).toBe(true);
    });

    test("false on mismatch + false when no selection", () => {
        const inst = _list();
        inst.previewState.recordId = 12;
        expect(inst.isPreviewSelected({resId: 5})).toBe(false);
        inst.previewState.recordId = null;
        expect(inst.isPreviewSelected({resId: 5})).toBe(false);
    });
});
