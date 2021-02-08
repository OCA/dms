/** ********************************************************************************
    Copyright 2020 Creu Blanca
    Copyright 2017-2019 MuK IT GmbH
    License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
 **********************************************************************************/

odoo.define("dms.FileKanbanController", function(require) {
    "use strict";

    var KanbanController = require("web.KanbanController");
    var preview = require("mail_preview_base.preview");
    var FieldPreviewViewer = preview.FieldPreviewViewer;
    var DragDrop = require("dms.DragDrop");

    var FileKanbanController = KanbanController.extend(
        _.extend(DragDrop, {
            custom_events: _.extend({}, KanbanController.prototype.custom_events, {
                preview_file: "_onPreviewFile",
            }),
            _onPreviewFile: function(ev) {
                var record = this.model.get(ev.data.id, {raw: true});
                var fieldName = "content";
                var mimetype = record.data.res_mimetype;
                var type = mimetype.split("/").shift();
                if (
                    type === "video" ||
                    type === "image" ||
                    mimetype === "application/pdf"
                ) {
                    var attachmentViewer = new FieldPreviewViewer(
                        this,
                        [
                            {
                                mimetype: record.data.res_mimetype,
                                id: record.data.id,
                                fileType: record.data.res_mimetype,
                                name: record.data.name,
                            },
                        ],
                        record.data.id,
                        this.modelName,
                        fieldName
                    );
                    attachmentViewer.appendTo($("body"));
                } else {
                    window.location =
                        "/web/content/" +
                        this.modelName +
                        "/" +
                        record.data.id +
                        "/" +
                        fieldName +
                        "/" +
                        record.data.name +
                        "?download=true";
                }
            },
        })
    );

    return FileKanbanController;
});
