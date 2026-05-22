// /** ********************************************************************************
//     Copyright 2020 Creu Blanca
//     Copyright 2026 ledoent — Don Kendall
//     License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
//  **********************************************************************************/

import {FilePreviewPane} from "../components/preview/file_preview_pane.esm";
import {ListRenderer} from "@web/views/list/list_renderer";
import {onMounted, onWillUnmount, useState} from "@odoo/owl";
import {readStored, writeStored} from "../utils/storage.esm";

// Side-pane toggle persists in localStorage so it survives navigation.
const DMS_LIST_PREVIEW_KEY = "dms_list_preview_pane";

function _readStoredPreview() {
    // Default: pane visible. Only the explicit "0" persisted by the user
    // clicking close keeps it hidden on subsequent loads.
    return readStored(DMS_LIST_PREVIEW_KEY) !== "0";
}

export class FileListRenderer extends ListRenderer {
    setup() {
        super.setup();
        this.previewState = useState({
            open: _readStoredPreview(),
            recordId: null,
        });
        // ESC closes the pane — global listener registered on mount.
        this._onKeyDown = (ev) => {
            if (ev.key === "Escape" && this.previewState.open) {
                if (this.previewState.recordId) {
                    this.closePreview();
                } else {
                    this.togglePreview();
                }
            }
        };
        onMounted(() => window.addEventListener("keydown", this._onKeyDown));
        onWillUnmount(() => window.removeEventListener("keydown", this._onKeyDown));
    }

    isPreviewSelected(record) {
        return this.previewState.recordId === record.resId;
    }

    togglePreview() {
        this.previewState.open = !this.previewState.open;
        writeStored(DMS_LIST_PREVIEW_KEY, this.previewState.open ? "1" : "0");
        if (!this.previewState.open) {
            this.previewState.recordId = null;
        }
    }

    closePreview() {
        // Full dismissal: header X button + Escape both route here and
        // users expect the pane to go away (not just clear the file).
        // Persist the closed state so the choice survives navigation.
        this.previewState.recordId = null;
        this.previewState.open = false;
        writeStored(DMS_LIST_PREVIEW_KEY, "0");
    }

    onCellClicked(record, column, ev) {
        // Row click always opens the side pane. The "Hide preview" toggle
        // hides the pane temporarily; the next row click reopens it. Users
        // who need the full form view click the "Open form" button in the
        // pane header (rendered by FilePreviewPane).
        if (record.resId) {
            this.previewState.open = true;
            this.previewState.recordId = record.resId;
            writeStored(DMS_LIST_PREVIEW_KEY, "1");
            ev?.stopPropagation?.();
            ev?.preventDefault?.();
            return;
        }
        return super.onCellClicked(record, column, ev);
    }

    // Adds an accent class to the row whose record is currently in the
    // preview pane. Called from the template via `t-att-class`.
    getRowClass(record) {
        const base = super.getRowClass(record);
        if (this.isPreviewSelected(record)) {
            return `${base || ""} o_dms_preview_selected_row`.trim();
        }
        return base;
    }
}

FileListRenderer.components = {
    ...FileListRenderer.components,
    FilePreviewPane,
};
