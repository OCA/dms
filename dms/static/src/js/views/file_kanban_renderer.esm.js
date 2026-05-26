// /** ********************************************************************************
//     Copyright 2020 Creu Blanca
//     Copyright 2026 ledoent — Don Kendall
//     License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
//  **********************************************************************************/
import {useExternalListener, useSubEnv} from "@odoo/owl";
import {FileKanbanRecord} from "./file_kanban_record.esm";
import {FilePreviewPane} from "../components/preview/file_preview_pane.esm";
import {KanbanRenderer} from "@web/views/kanban/kanban_renderer";
import {useDmsPreviewState, useStoredState} from "../utils/use_stored_state.esm";

// Density tiers: "comfortable" (default), "compact", "list".
export const DMS_KANBAN_DEFAULT_DENSITY = "comfortable";
const DMS_KANBAN_DENSITY_KEY = "dms_kanban_density";
const DMS_KANBAN_PREVIEW_KEY = "dms_kanban_preview_pane";
const DMS_KANBAN_DENSITY_OPTIONS = [
    {value: "comfortable", label: "Comfortable", icon: "fa-th-large"},
    {value: "compact", label: "Compact", icon: "fa-th"},
    {value: "list", label: "List", icon: "fa-bars"},
];
const DMS_DENSITY_VALUES = new Set(DMS_KANBAN_DENSITY_OPTIONS.map((o) => o.value));

export class FileKanbanRenderer extends KanbanRenderer {
    static template = "dms.KanbanRenderer";
    static components = {
        ...KanbanRenderer.components,
        KanbanRecord: FileKanbanRecord,
        FilePreviewPane,
    };

    setup() {
        super.setup();
        // Density: persisted string with tampered-value defence.
        this._density = useStoredState(
            DMS_KANBAN_DENSITY_KEY,
            DMS_KANBAN_DEFAULT_DENSITY,
            {
                deserializer: (v) =>
                    DMS_DENSITY_VALUES.has(v) ? v : DMS_KANBAN_DEFAULT_DENSITY,
            }
        );
        // Side-pane: shared with the list renderer via useDmsPreviewState.
        this.previewState = useDmsPreviewState(DMS_KANBAN_PREVIEW_KEY);
        // Expose select callback to descendant FileKanbanRecord instances via
        // env so card clicks route into the renderer's preview state without
        // the records needing a direct reference up the tree.
        useSubEnv({
            dmsKanbanPreview: {
                select: (resId) => this.previewState.select(resId),
                isOpen: () => this.previewState.open,
            },
        });
        useExternalListener(window, "keydown", (ev) => {
            if (ev.key === "Escape" && this.previewState.open) {
                this.closePreview();
            }
        });
    }

    get density() {
        return this._density.value;
    }

    get densityOptions() {
        return DMS_KANBAN_DENSITY_OPTIONS;
    }

    setDensity(value) {
        this._density.value = value;
    }

    togglePreview() {
        this.previewState.toggle();
    }

    closePreview() {
        this.previewState.close();
    }
}
