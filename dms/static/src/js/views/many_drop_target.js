/* global base64js*/
/* Copyright 2020 Creu Blanca
 * Copyright 2021 Tecnativa - Alexandre D. Díaz
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl). */
odoo.define("dms.DragDrop", function (require) {
    "use strict";

    const DropTargetMixin = require("web_drop_target");
    const core = require("web.core");
    const _t = core._t;

    return _.extend({}, DropTargetMixin.DropTargetMixin, {
        /**
         * @override
         */
        init: function () {
            this._super.apply(this, arguments);
            this._get_directory_id(
                this._searchPanel ? this._searchPanel.getDomain() : []
            );
        },
        _drop_zone_selector: ".o_kanban_view",
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
            // Don't need the record id to work
            return true;
        },

        /**
         * @override
         */
        _create_attachment: function (file, reader, res_model) {
            // Helper to upload an attachment and update the sidebar
            const ctx = this.renderer.state.getContext();
            console.log(ctx);
            if (this.directory_id) {
                ctx.default_directory_id = this.directory_id;
            }
            console.log(ctx);
            if (typeof ctx.default_directory_id === "undefined") {
                return this.displayNotification({
                    message: _t("You must select a directory first"),
                    type: "danger",
                });
            }
            return this._rpc({
                model: res_model,
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
            }).then(() => this.reload());
        },

        /**
         * @private
         * @param {Array} domain
         */
        _get_directory_id: function (domain) {
            let directory_id = false;
            _.each(domain, (leaf) => {
                if (
                    leaf[0] === "directory_id" &&
                    (leaf[1] === "child_of" || leaf[1] === "=")
                ) {
                    directory_id = leaf[2];
                }
            });
            this.directory_id = directory_id;
        },

        /**
         * @override
         */
        _update: function (state, params) {
            this._get_directory_id(params.domain);
            return this._super.apply(this, arguments).then((result) => {
                this._update_overlay();
                return result;
            });
        },
    });
});
