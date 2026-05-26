// /** ********************************************************************************
//     Copyright 2020 Creu Blanca
//     Copyright 2026 ledoent — Don Kendall
//     License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
//  **********************************************************************************/
import {useExternalListener, useState, useSubEnv} from "@odoo/owl";
import {FileKanbanRecord} from "./file_kanban_record.esm";
import {FilePreviewPane} from "../components/preview/file_preview_pane.esm";
import {KanbanRenderer} from "@web/views/kanban/kanban_renderer";
import {readStored, writeStored} from "../utils/storage.esm";

// Density tiers: "comfortable" (default), "compact", "list".
// Selected value is persisted per-browser via localStorage so it survives
// kanban→form→kanban navigation; sharing across browsers / users is out of
// scope for this iteration.
export const DMS_KANBAN_DEFAULT_DENSITY = "comfortable";
const DMS_KANBAN_DENSITY_KEY = "dms_kanban_density";
const DMS_KANBAN_PREVIEW_KEY = "dms_kanban_preview_pane";
const DMS_KANBAN_DENSITY_OPTIONS = [
    {value: "comfortable", label: "Comfortable", icon: "fa-th-large"},
    {value: "compact", label: "Compact", icon: "fa-th"},
    {value: "list", label: "List", icon: "fa-bars"},
];

function _readStoredDensity() {
    // Validate against the option set — a user-tampered localStorage value
    // shouldn't crash the renderer or render an unknown density token in
    // the [data-density] attribute (which would silently skip our CSS).
    const stored = readStored(DMS_KANBAN_DENSITY_KEY);
    if (stored && DMS_KANBAN_DENSITY_OPTIONS.some((o) => o.value === stored)) {
        return stored;
    }
    return DMS_KANBAN_DEFAULT_DENSITY;
}

function _readStoredPreview() {
    // Default: pane visible. Only the explicit "0" persisted by the user
    // clicking close keeps it hidden on subsequent loads.
    return readStored(DMS_KANBAN_PREVIEW_KEY) !== "0";
}

export class FileKanbanRenderer extends KanbanRenderer {
    static template = "dms.KanbanRenderer";
    static components = {
        ...KanbanRenderer.components,
        KanbanRecord: FileKanbanRecord,
        FilePreviewPane,
    };

    setup() {
        super.setup();
        this.densityState = useState({density: _readStoredDensity()});
        this.previewState = useState({
            open: _readStoredPreview(),
            recordId: null,
        });
        // Expose select callback to descendant FileKanbanRecord instances via
        // env so card clicks route into the renderer's preview state without
        // the records needing a direct reference up the tree.
        useSubEnv({
            dmsKanbanPreview: {
                select: (resId) => this.selectForPreview(resId),
                isOpen: () => this.previewState.open,
            },
        });
        // Esc dismisses the pane. `useExternalListener` auto-binds + cleans
        // up on unmount — replaces the prior manual onMounted/onWillUnmount
        // pair plus an instance-level handler ref. One hook, idiomatic OWL 2.
        useExternalListener(window, "keydown", (ev) => {
            if (ev.key === "Escape" && this.previewState.open) {
                this.closePreview();
            }
        });
    }

    get density() {
        return this.densityState.density;
    }

    get densityOptions() {
        return DMS_KANBAN_DENSITY_OPTIONS;
    }

    setDensity(value) {
        this.densityState.density = value;
        writeStored(DMS_KANBAN_DENSITY_KEY, value);
    }

    togglePreview() {
        this.previewState.open = !this.previewState.open;
        writeStored(DMS_KANBAN_PREVIEW_KEY, this.previewState.open ? "1" : "0");
        if (!this.previewState.open) {
            this.previewState.recordId = null;
        }
    }

    closePreview() {
        // The pane header's X button + Escape key both route here. Users
        // expect a full dismissal (pane goes away), not just a deselect
        // — clearing recordId only would leave the pane mounted in its
        // empty "Click any row to preview" state, which reads as "the
        // close button is broken." Persist the closed state so the pane
        // stays hidden after navigation, mirroring `togglePreview()`.
        this.previewState.recordId = null;
        this.previewState.open = false;
        writeStored(DMS_KANBAN_PREVIEW_KEY, "0");
    }

    selectForPreview(resId) {
        if (!resId) {
            return;
        }
        this.previewState.open = true;
        this.previewState.recordId = resId;
        writeStored(DMS_KANBAN_PREVIEW_KEY, "1");
    }
}
