// /** ********************************************************************************
//     Copyright 2024 Subteno - Timothée Vannier (https://www.subteno.com).
//     Copyright 2026 ledoent — Don Kendall
//     License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
//  **********************************************************************************/
import {KanbanRecord} from "@web/views/kanban/kanban_record";
import {useService} from "@web/core/utils/hooks";
import {useState} from "@odoo/owl";

export class FileKanbanRecord extends KanbanRecord {
    setup() {
        super.setup();
        // Inline-rename state (F3). Double-click the name → swap label for
        // input → Enter commits, Esc cancels, blur commits-or-cancels based
        // on whether the draft actually changed. Matches the macOS Finder /
        // GNOME Files convention.
        this.renameState = useState({active: false, draft: ""});
        this.notification = useService("notification");
    }

    /**
     * @override
     *
     * Every kanban click — including the file icon — routes through the
     * renderer's side-pane preview state. Previously the icon had its own
     * branch that opened Odoo's built-in modal `fileViewer`; that detour
     * was inconsistent with the rest of the card (which already selected
     * for the side-pane) and meant the registered handler chain in
     * `dms.preview_handlers` never saw the click.
     *
     * In rename mode, swallow clicks so they don't dismiss the input.
     */
    onGlobalClick(ev) {
        if (this.renameState.active) {
            ev.preventDefault?.();
            ev.stopPropagation?.();
            return;
        }
        if (this.env.dmsKanbanPreview && this.props.record.resId) {
            this.env.dmsKanbanPreview.select(this.props.record.resId);
            ev.preventDefault?.();
            ev.stopPropagation?.();
            return;
        }
        return super.onGlobalClick(ev);
    }

    startRename(ev) {
        // Don't let the dblclick bubble to onGlobalClick — that would open
        // the preview pane on top of our input.
        ev?.stopPropagation?.();
        ev?.preventDefault?.();
        this.renameState.draft = this.props.record.data.name || "";
        this.renameState.active = true;
    }

    cancelRename() {
        this.renameState.active = false;
        this.renameState.draft = "";
    }

    async commitRename() {
        const next = (this.renameState.draft || "").trim();
        const current = this.props.record.data.name || "";
        if (!next || next === current) {
            this.cancelRename();
            return;
        }
        try {
            await this.props.record.update({name: next});
            await this.props.record.save({noReload: true, savePoint: false});
        } catch (e) {
            this.notification.add(e.message || "Rename failed", {type: "danger"});
            this.cancelRename();
            return;
        }
        this.cancelRename();
    }

    onRenameKeydown(ev) {
        if (ev.key === "Enter") {
            ev.preventDefault();
            this.commitRename();
        } else if (ev.key === "Escape") {
            ev.preventDefault();
            this.cancelRename();
        }
        // Stop propagation so the renderer-level Escape (which closes the
        // preview pane) doesn't also fire from inside the rename input.
        ev.stopPropagation();
    }

    onRenameInput(ev) {
        this.renameState.draft = ev.target.value;
    }
}
