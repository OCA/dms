// Copyright 2026 ledoent — Don Kendall
// License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import {DmsDirectoryKanbanRenderer} from "./dms_directory_kanban_renderer.esm";
import {kanbanView} from "@web/views/kanban/kanban_view";
import {registry} from "@web/core/registry";

export const DmsDirectoryKanbanView = {
    ...kanbanView,
    Renderer: DmsDirectoryKanbanRenderer,
};

registry.category("views").add("dms_directory_kanban", DmsDirectoryKanbanView);
