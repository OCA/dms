/** ********************************************************************************
    Copyright 2020 Creu Blanca
    Copyright 2017-2019 MuK IT GmbH
    License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
 **********************************************************************************/

odoo.define("dms.preview", function(require) {
    "use strict";

    var basic_fields = require("web.basic_fields");
    var registry = require("web.field_registry");
    var core = require("web.core");
    var DocumentViewer = require("mail.DocumentViewer");

    var QWeb = core.qweb;

    var FieldPreviewViewer = DocumentViewer.extend({
        template: "FieldBinaryPreview",
        init: function(parent, attachments, activeAttachmentID, model, field) {
            this._super.apply(this, arguments);
            this.modelName = model;
            this.fieldName = field;
        },
        /*
            We need to overwrite this function in order to ensure that the
            correct template is used
        */
        _updateContent: function() {
            this.$(".o_viewer_content").html(
                QWeb.render("FieldBinaryPreview.Content", {widget: this})
            );
            this.$(".o_viewer_img").on("load", _.bind(this._onImageLoaded, this));
            this.$('[data-toggle="tooltip"]').tooltip({delay: 0});
            this._reset();
        },
        _onDownload: function(e) {
            e.preventDefault();
            var url = new URL(
                "/web/content/" +
                    this.modelName +
                    "/" +
                    this.activeAttachment.id +
                    "/" +
                    this.fieldName,
                window.location.href
            );
            url.searchParams.set("download", true);
            url.searchParams.set("filename", this.activeAttachment.name);
            window.location = url.href;
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
                        name: this.filename_value,
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
