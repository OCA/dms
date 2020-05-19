/** ********************************************************************************
    Copyright 2020 Creu Blanca
    Copyright 2017-2019 MuK IT GmbH
    License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
 **********************************************************************************/

odoo.define("dms.FileKanbanController", function(require) {
    "use strict";

    var KanbanController = require("web.KanbanController");
    var DragDrop = require("dms.DragDrop");

    var FileKanbanController = KanbanController.extend(DragDrop);

    return FileKanbanController;
});
