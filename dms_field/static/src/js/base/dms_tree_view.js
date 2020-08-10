odoo.define("dms.DmsTreeView", function(require) {
    "use strict";

    var BasicView = require("web.BasicView");

    var DmsTreeController = require("dms.DmsTreeController");
    var DmsTreeRenderer = require("dms.DmsTreeRenderer");
    var view_registry = require("web.view_registry");
    var core = require("web.core");
    var _lt = core._lt;

    var DmsTreeView = BasicView.extend({
        display_name: _lt("DMS"),
        icon: "fa-tachometer",
        template: "dms.DocumentTree",
        viewType: "dms_tree",
        config: _.extend({}, BasicView.prototype.config, {
            Controller: DmsTreeController,
            Renderer: DmsTreeRenderer,
        }),
        multi_record: true,
        searchable: false,
    });

    view_registry.add("dms_tree", DmsTreeView);

    return DmsTreeView;
});
