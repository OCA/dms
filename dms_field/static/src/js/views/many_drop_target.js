/* global base64js*/
/* Copyright 2024 Tecnativa - Carlos Roca
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl). */
odoo.define("dms_field.DragDrop", function (require) {
    "use strict";

    const DropTargetMixin = require("web_drop_target");

    return _.extend({}, DropTargetMixin.DropTargetMixin, {
        _drop_zone_selector: ".dms_document_preview",

        /**
         * @override
         */
        _handle_drop_items: function (drop_items) {
            _.each(drop_items, this._handle_file_drop_attach, this);
        },

        /**
         * @override
         */
        _get_record_id: function () {
            return true;
        },

        _get_selection_id: function () {
            return this.$drop_zone
                .find(".o_preview_directory")
                .attr("data-directory-id");
        },

        /**
         * @override
         */
        _checkDragOver: function () {
            return Boolean(this._get_selection_id());
        },

        /**
         * @override
         */
        _create_attachment: function (file, reader) {
            // Helper to upload an attachment and update the sidebar
            const ctx = this.renderer.state.getContext();
            const directory = parseInt(this._get_selection_id());
            if (this._checkDragOver()) {
                ctx.default_directory_id = directory;
            }
            return this._rpc({
                model: "dms.file",
                method: "create",
                args: [
                    {
                        name: file.name,
                        content: base64js.fromByteArray(new Uint8Array(reader.result)),
                    },
                ],
                kwargs: {
                    context: ctx,
                },
            }).then(() => {
                const selected_id = $(".jstree-clicked").attr("id");
                this.$(".dms_tree").jstree(true).refresh_node(selected_id);
            });
        },
    });
});
