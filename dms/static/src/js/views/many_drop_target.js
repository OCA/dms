/* global Uint8Array base64js*/
odoo.define("dms.DragDrop", function(require) {
    "use strict";

    var DropTargetMixin = require("web_drop_target");
    var core = require("web.core");
    var qweb = core.qweb;

    return _.extend(DropTargetMixin.DropTargetMixin, {
        _get_drop_items: function(e) {
            var self = this,
                dataTransfer = e.originalEvent.dataTransfer,
                drop_items = [];
            _.each(dataTransfer.files, function(item) {
                if (
                    _.contains(self._drop_allowed_types, item.type) ||
                    _.isEmpty(self._drop_allowed_types)
                ) {
                    drop_items.push(item);
                }
            });
            return drop_items;
        },
        _handle_drop_items: function(drop_items, e) {
            var self = this;
            _.each(drop_items, function(item) {
                return self._handle_file_drop(item, e, self.renderer.state.model);
            });
        },
        _handle_file_drop: function(item, event, model) {
            var self = this;
            var file = item;
            if (!file || !(file instanceof Blob)) {
                return;
            }
            var reader = new FileReader();
            reader.onloadend = self.proxy(
                _.partial(self._create_file, file, reader, event, model)
            );
            reader.onerror = self.proxy("_file_reader_error_handler");
            reader.readAsArrayBuffer(file);
        },
        _add_overlay: function() {
            if (!this._drop_overlay) {
                var o_content = jQuery(".o_content"),
                    view_manager = jQuery(".o_view_manager_content");
                this._drop_overlay = jQuery(qweb.render("dms.drop_overlay"));
                var o_content_position = o_content.position();
                this._drop_overlay.css({
                    top: o_content_position.top,
                    left: o_content_position.left,
                    width: view_manager.width(),
                    height: view_manager.height(),
                });
                o_content.append(this._drop_overlay);
            }
        },
        _create_file: function(file, reader, event, model) {
            // Helper to upload an attachment and update the sidebar
            var self = this;
            return this._rpc({
                model: model,
                method: "create",
                args: [
                    {
                        name: file.name,
                        content: base64js.fromByteArray(new Uint8Array(reader.result)),
                    },
                ],
                kwargs: {
                    context: this.model.get(this.handle, {raw: true}).getContext(),
                },
            }).then(function() {
                self.reload();
            });
        },
    });
});
