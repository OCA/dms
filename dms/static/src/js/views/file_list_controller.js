/** ********************************************************************************
    Copyright 2020 Creu Blanca
    Copyright 2017-2019 MuK IT GmbH
    License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
 **********************************************************************************/

odoo.define("dms.FileListController", function (require) {
    "use strict";

    var ListController = require("web.ListController");
    var DragDrop = require("dms.DragDrop");

    var FileListController = ListController.extend(DragDrop);

    return FileListController;
});
