/** ********************************************************************************
    Copyright 2020 Creu Blanca
    License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
 **********************************************************************************/

odoo.define("dms.FileKanbanRenderer", function(require) {
    "use strict";

    var KanbanRenderer = require("web.KanbanRenderer");

    var FileKanbanRenderer = KanbanRenderer.extend({
        events: _.extend({}, KanbanRenderer.prototype.events || {}, {
            "click .o_kanban_dms_file_preview": "_onRecordPreview",
        }),
        _onRecordPreview: function(ev) {
            ev.stopPropagation();
            var id = $(ev.currentTarget).data("id");
            if (id) {
                this.trigger_up("preview_file", {
                    id: id,
                    target: ev.target,
                });
            }
        },
    });

    return FileKanbanRenderer;
});
