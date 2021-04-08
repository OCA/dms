/** ********************************************************************************
    Copyright 2020 Creu Blanca
    Copyright 2017-2019 MuK IT GmbH
    License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
 **********************************************************************************/

odoo.define("dms.FileKanbanView", function (require) {
    "use strict";

    var registry = require("web.view_registry");

    var KanbanView = require("web.KanbanView");

    var FileKanbanController = require("dms.FileKanbanController");

    var FileKanbanRenderer = require("dms.FileKanbanRenderer");

    var FileKanbanView = KanbanView.extend({
        config: _.extend({}, KanbanView.prototype.config, {
            Controller: FileKanbanController,
            Renderer: FileKanbanRenderer,
        }),
    });

    registry.add("file_kanban", FileKanbanView);

    return FileKanbanView;
});
