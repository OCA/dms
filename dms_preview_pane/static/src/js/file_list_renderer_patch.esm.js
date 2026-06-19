// Copyright 2026 ledoent - Don Kendall
// License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import {FileListRenderer} from "@dms/js/views/file_list_renderer.esm";
import {FilePreviewPane} from "./components/preview/file_preview_pane.esm";
import {patch} from "@web/core/utils/patch";
import {useDmsPreviewState} from "./utils/use_stored_state.esm";
import {useExternalListener} from "@odoo/owl";

// Toggle state persists in localStorage so it survives navigation.
const DMS_LIST_PREVIEW_KEY = "dms_list_preview_pane";

// Extend the dms list renderer in place (no fork of dms): add the preview
// state + row-click → select wiring, and swap the template for a split-layout
// wrapper that t-calls the original `dms.ListRenderer`.
patch(FileListRenderer.prototype, {
    setup() {
        super.setup();
        this.previewState = useDmsPreviewState(DMS_LIST_PREVIEW_KEY);
        useExternalListener(window, "keydown", (ev) => {
            if (ev.key === "Escape" && this.previewState.open) {
                this.closePreview();
            }
        });
    },

    isPreviewSelected(record) {
        return this.previewState.recordId === record.resId;
    },

    togglePreview() {
        this.previewState.toggle();
    },

    closePreview() {
        this.previewState.close();
    },

    onCellClicked(record, column, ev) {
        // Row click opens the side pane; "Open form" in the pane header
        // navigates to the full form view when needed.
        if (record.resId) {
            this.previewState.select(record.resId);
            ev?.stopPropagation?.();
            ev?.preventDefault?.();
            return;
        }
        return super.onCellClicked(record, column, ev);
    },

    getRowClass(record) {
        const base = super.getRowClass(record);
        if (this.isPreviewSelected(record)) {
            return `${base || ""} o_dms_preview_selected_row`.trim();
        }
        return base;
    },
});

FileListRenderer.components = {
    ...FileListRenderer.components,
    FilePreviewPane,
};
FileListRenderer.template = "dms_preview_pane.ListRenderer";
