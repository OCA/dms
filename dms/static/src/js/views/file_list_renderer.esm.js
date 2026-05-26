// /** ********************************************************************************
//     Copyright 2020 Creu Blanca
//     Copyright 2026 ledoent — Don Kendall
//     License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
//  **********************************************************************************/

import {FilePreviewPane} from "../components/preview/file_preview_pane.esm";
import {ListRenderer} from "@web/views/list/list_renderer";
import {useExternalListener} from "@odoo/owl";
import {useDmsPreviewState} from "../utils/use_stored_state.esm";

// Side-pane toggle persists in localStorage so it survives navigation.
const DMS_LIST_PREVIEW_KEY = "dms_list_preview_pane";

export class FileListRenderer extends ListRenderer {
    static template = "dms.ListRenderer";
    static components = {
        ...ListRenderer.components,
        FilePreviewPane,
    };

    setup() {
        super.setup();
        // `useDmsPreviewState` encapsulates the open/recordId/toggle/close/select
        // machinery shared with the kanban renderer. Templates read .open /
        // .recordId; methods below shim to .toggle() / .close() so XML doesn't
        // need to know about the hook.
        this.previewState = useDmsPreviewState(DMS_LIST_PREVIEW_KEY);
        useExternalListener(window, "keydown", (ev) => {
            if (ev.key === "Escape" && this.previewState.open) {
                this.closePreview();
            }
        });
    }

    isPreviewSelected(record) {
        return this.previewState.recordId === record.resId;
    }

    togglePreview() {
        this.previewState.toggle();
    }

    closePreview() {
        this.previewState.close();
    }

    onCellClicked(record, column, ev) {
        // Row click always opens the side pane. The "Hide preview" toggle
        // hides the pane temporarily; the next row click reopens it. Users
        // who need the full form view click the "Open form" button in the
        // pane header (rendered by FilePreviewPane).
        if (record.resId) {
            this.previewState.select(record.resId);
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
