/** ********************************************************************************
    Copyright 2020 Creu Blanca
    Copyright 2017-2019 MuK IT GmbH
    License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
 **********************************************************************************/

odoo.define("dms.preview", function(require) {
    "use strict";

    var basic_fields = require("web.basic_fields");
    var registry = require("web.field_registry");
    var DocumentViewer = require("mail.DocumentViewer");

    var FieldPreviewViewer = DocumentViewer.extend({
        template: "FieldBinaryPreview",
        init: function(parent, attachments, activeAttachmentID, model, field) {
            this._super.apply(this, arguments);
            this.modelName = model;
            this.fieldName = field;
        },
        _onDownload: function(e) {
            e.preventDefault();
            window.location =
                "/web/content/" +
                this.modelName +
                "/" +
                this.activeAttachment.id +
                "/" +
                this.fieldName +
                "/" +
                "datas" +
                "?download=true";
        },
    });

    var FieldPreviewBinary = basic_fields.FieldBinaryFile.extend({
        events: _.extend({}, basic_fields.FieldBinaryFile.prototype.events, {
            "click .preview_file": "_previewFile",
        }),
        _previewFile: function(event) {
            event.stopPropagation();
            event.preventDefault();
            var attachmentViewer = new FieldPreviewViewer(
                this,
                [
                    {
                        mimetype: this.recordData.res_mimetype,
                        id: this.res_id,
                        fileType: this.recordData.res_mimetype,
                        name: this.filename,
                    },
                ],
                this.res_id,
                this.model,
                this.name
            );
            attachmentViewer.appendTo($("body"));
        },
        _renderReadonly: function() {
            this._super.apply(this, arguments);
            if (this.value) {
                var mimetype = this.recordData.res_mimetype;
                var type = mimetype.split("/").shift();
                if (
                    type === "video" ||
                    type === "image" ||
                    mimetype === "application/pdf"
                ) {
                    this.$el.prepend(
                        $("<span/>").addClass("fa fa-search preview_file")
                    );
                }
            }
        },
    });

    registry.add("preview_binary", FieldPreviewBinary);

    return {
        FieldPreviewViewer: FieldPreviewViewer,
        FieldPreviewBinary: FieldPreviewBinary,
    };
});
