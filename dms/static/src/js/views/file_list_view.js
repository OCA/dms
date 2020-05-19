/** ********************************************************************************
    Copyright 2020 Creu Blanca
    Copyright 2017-2019 MuK IT GmbH
    License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
 **********************************************************************************/

odoo.define("dms.FileListView", function(require) {
    "use strict";
    var registry = require("web.view_registry");

    var ListView = require("web.ListView");

    var FileListController = require("dms.FileListController");

    var FileListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: FileListController,
        }),
    });

    registry.add("file_list", FileListView);

    return FileListView;
});
