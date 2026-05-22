// Copyright 2026 ledoent — Don Kendall
// License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import {KanbanRenderer} from "@web/views/kanban/kanban_renderer";
import {DmsStatBar} from "../components/dms_stat_bar.esm";
import {onWillStart, useState} from "@odoo/owl";
import {useService} from "@web/core/utils/hooks";

export class DmsDirectoryKanbanRenderer extends KanbanRenderer {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.statsState = useState({stats: null});
        onWillStart(async () => {
            this.statsState.stats = await this.orm.call(
                "dms.directory",
                "get_dashboard_stats",
                []
            );
        });
    }

    get stats() {
        return this.statsState.stats;
    }
}

DmsDirectoryKanbanRenderer.components = {
    ...KanbanRenderer.components,
    DmsStatBar,
};
DmsDirectoryKanbanRenderer.template = "dms.DirectoryKanbanRenderer";
