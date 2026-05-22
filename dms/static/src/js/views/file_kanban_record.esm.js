// /** ********************************************************************************
//     Copyright 2024 Subteno - Timothée Vannier (https://www.subteno.com).
//     Copyright 2026 ledoent — Don Kendall
//     License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
//  **********************************************************************************/
import {KanbanRecord} from "@web/views/kanban/kanban_record";

export class FileKanbanRecord extends KanbanRecord {
    /**
     * @override
     *
     * Every kanban click — including the file icon — routes through the
     * renderer's side-pane preview state. Previously the icon had its own
     * branch that opened Odoo's built-in modal `fileViewer`; that detour
     * was inconsistent with the rest of the card (which already selected
     * for the side-pane) and meant the registered handler chain in
     * `dms.preview_handlers` never saw the click.
     */
    onGlobalClick(ev) {
        if (this.env.dmsKanbanPreview && this.props.record.resId) {
            this.env.dmsKanbanPreview.select(this.props.record.resId);
            ev.preventDefault?.();
            ev.stopPropagation?.();
            return;
        }
        return super.onGlobalClick(ev);
    }
}
