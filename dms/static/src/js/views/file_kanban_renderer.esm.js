// /** ********************************************************************************
//     Copyright 2020 Creu Blanca
//     License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
//  **********************************************************************************/
import {FileKanbanRecord} from "./file_kanban_record.esm";
import {KanbanRenderer} from "@web/views/kanban/kanban_renderer";

export class FileKanbanRenderer extends KanbanRenderer {
    static template = "dms.KanbanRenderer";
    static components = {
        ...KanbanRenderer.components,
        KanbanRecord: FileKanbanRecord,
    };
}
