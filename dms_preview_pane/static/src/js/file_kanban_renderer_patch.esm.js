// Copyright 2026 ledoent - Don Kendall
// License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import {FileKanbanRecord} from "@dms/js/views/file_kanban_record.esm";
import {FileKanbanRenderer} from "@dms/js/views/file_kanban_renderer.esm";
import {FilePreviewPane} from "./components/preview/file_preview_pane.esm";
import {patch} from "@web/core/utils/patch";
import {useDmsPreviewState} from "./utils/use_stored_state.esm";
import {useExternalListener, useSubEnv} from "@odoo/owl";

const DMS_KANBAN_PREVIEW_KEY = "dms_kanban_preview_pane";

// Extend the dms kanban renderer in place: add the preview state + a split
// template that t-calls the original `dms.KanbanRenderer`. Card clicks route
// into the preview state via a sub-env channel the FileKanbanRecord reads.
patch(FileKanbanRenderer.prototype, {
    setup() {
        super.setup();
        this.previewState = useDmsPreviewState(DMS_KANBAN_PREVIEW_KEY);
        useSubEnv({
            dmsKanbanPreview: {
                select: (resId) => this.previewState.select(resId),
                isOpen: () => this.previewState.open,
                selectedId: () =>
                    this.previewState.open ? this.previewState.recordId : null,
                notifyChanged: (resId) => this.previewState.notifyChanged(resId),
            },
        });
        useExternalListener(window, "keydown", (ev) => {
            if (ev.key === "Escape" && this.previewState.open) {
                this.closePreview();
            }
        });
    },

    togglePreview() {
        this.previewState.toggle();
    },

    closePreview() {
        this.previewState.close();
    },
});

FileKanbanRenderer.components = {
    ...FileKanbanRenderer.components,
    FilePreviewPane,
};
FileKanbanRenderer.template = "dms_preview_pane.KanbanRenderer";

// Card click opens the side pane (instead of the form); the active card gets
// the same accent as the list's selected row.
patch(FileKanbanRecord.prototype, {
    getRecordClasses() {
        let classes = super.getRecordClasses();
        const selectedId = this.env.dmsKanbanPreview?.selectedId?.();
        if (selectedId && selectedId === this.props.record.resId) {
            classes += " o_dms_preview_selected_card";
        }
        return classes;
    },

    onGlobalClick(ev) {
        if (this.env.dmsKanbanPreview && this.props.record.resId) {
            this.env.dmsKanbanPreview.select(this.props.record.resId);
            ev.preventDefault?.();
            ev.stopPropagation?.();
            return;
        }
        return super.onGlobalClick(ev);
    },
});
