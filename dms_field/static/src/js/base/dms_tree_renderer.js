odoo.define("dms.DmsTreeRenderer", function (require) {
    "use strict";

    var BasicRenderer = require("web.BasicRenderer");
    var core = require("web.core");
    var ajax = require("web.ajax");
    var dialogs = require("web.view_dialogs");
    var config = require("web.config");

    var framework = require("web.framework");
    var session = require("web.session");
    var QWeb = core.qweb;
    var _t = core._t;

    var DmsTreeRenderer = BasicRenderer.extend({
        xmlDependencies: ["/dms_field/static/src/xml/tree.xml"],
        cssLibs: ["/dms_field/static/lib/jsTree/themes/proton/style.css"],
        jsLibs: ["/dms_field/static/lib/jsTree/jstree.js"],
        custom_events: _.extend({}, BasicRenderer.prototype.custom_events, {
            tree_changed: "_treeChanged",
        }),
        events: _.extend({}, BasicRenderer.prototype.events || {}, {
            "click .o_preview_file": "_onRecordPreview",
            "click .o_open_file": "_onOpenRecord",
            "click .o_dms_add_directory": "_onDMSAddDirectoryRecord",
        }),
        template: "dms.DocumentTree",
        init: function (parent, params) {
            // eslint-disable-next-line no-param-reassign
            params = _.defaults({}, params, {
                viewType: "dms_tree",
            });
            this._super.apply(this, arguments);
            this.params = params || {};
            this.storage_data = {};
            this.isMobile = config.device.isMobile;
        },
        willStart: function () {
            this.config = this._buildTreeConfig();
            return $.when(ajax.loadLibs(this), this._super.apply(this, arguments));
        },
        _buildTreeConfig: function () {
            var plugins = this.params.plugins || [
                "conditionalselect",
                "massload",
                "wholerow",
                "state",
                "sort",
                "search",
                "types",
                "contextmenu",
            ];
            var tree_config = {
                core: {
                    widget: this,
                    animation: this.params.animation || 0,
                    multiple: false,
                    check_callback:
                        this.params.check_callback || this._checkCallback.bind(this),
                    themes: this.params.themes || {
                        name: "proton",
                        responsive: true,
                    },
                    data: this._loadData.bind(this),
                },
                contextmenu: this.params.contextmenu_items || {
                    items: this._loadContextMenu.bind(this),
                },
                state: {
                    key: this.params.key || "documents",
                },
                conditionalselect:
                    this.params.conditionalselect || this._checkSelect.bind(this),
                plugins: plugins,
                sort: function (a, b) {
                    // Correctly sort the records according to the type of element
                    // (folder or file).
                    // Do not use node.icon because they may have (or will have) a
                    // different icon for each file according to its extension.
                    var node_a = this.get_node(a);
                    var node_b = this.get_node(b);
                    if (node_a.data.model === node_b.data.model) {
                        return node_a.text > node_b.text ? 1 : -1;
                    }
                    return node_a.data.model > node_b.data.model ? 1 : -1;
                },
            };
            return tree_config;
        },
        _loadData: function (node, callback) {
            this.trigger_up("dms_load", {
                node: node,
                callback: callback,
            });
        },
        start_tree_triggers: function () {
            var self = this;
            this.$tree.on("open_node.jstree", function (e, data) {
                if (data.node.data && data.node.data.model === "dms.directory") {
                    data.instance.set_icon(data.node, "fa fa-folder-open-o");
                }
            });
            this.$tree.on("close_node.jstree", function (e, data) {
                if (data.node.data && data.node.data.model === "dms.directory") {
                    data.instance.set_icon(data.node, "fa fa-folder-o");
                }
            });
            this.$tree.on("ready.jstree", function (e, data) {
                self.trigger_up("tree_ready", {
                    data: data,
                });
            });
            this.$tree.on("changed.jstree", function (e, data) {
                self.trigger_up("tree_changed", {
                    data: data,
                });
            });
            this.$tree.on("move_node.jstree", function (e, data) {
                var jstree = self.$tree.jstree(true);
                self.trigger_up("dms_move_node", {
                    node: data.node,
                    new_parent: jstree.get_node(data.parent),
                    old_parent: data.old_parent,
                });
            });
            this.$tree.on("rename_node.jstree", function (e, data) {
                self.trigger_up("dms_rename_node", {
                    node: data.node,
                    text: data.text,
                    old: data.old,
                });
                self._preview_node(data.node);
            });
            this.$tree.on("delete_node.jstree", function (e, data) {
                self.trigger_up("dms_delete_node", {
                    node: data.node,
                    parent: data.parent,
                });
            });
            this.$tree.on("loaded.jstree", () => {
                this.$tree.jstree("open_all");
            });
            this.$('[data-toggle="tooltip"]').tooltip();
        },
        _treeChanged: function (ev) {
            var data = ev.data.data;
            if (data.selected && data.selected.length === 1) {
                this._preview_node(data.node);
            }
        },
        start: function () {
            var res = this._super.apply(this, arguments);
            this.$tree = this.$(".dms_tree");
            this.$tree.jstree(this.config);
            this.start_tree_triggers();
            return res;
        },
        /*
            This is used to check that the operation is allowed
        */
        _checkCallback: function (operation, node, parent) {
            if (operation === "copy_node" || operation === "move_node") {
                // Prevent moving a root node
                if (node.parent === "#") {
                    return false;
                }
                // Prevent moving a child above or below the root
                if (parent.id === "#") {
                    return false;
                }
                // Prevent moving a child to a settings object
                if (parent.data && parent.data.model === "dms.storage") {
                    return false;
                }
                // Prevent moving a child to a file
                if (parent.data && parent.data.model === "dms.file") {
                    return false;
                }
            }
            return true;
        },
        _checkSelect: function (node) {
            if (this.params.filesOnly && node.data.model !== "dms.file") {
                return false;
            }
            return !(node.parent === "#" && node.data.model === "dms.storage");
        },
        _preview_node: function (node) {
            var $buttons = this.$el.find(".o_dms_extra_actions");
            $buttons.empty();
            if (
                node.data &&
                ["dms.directory", "dms.file"].indexOf(node.data.model) !== -1
            ) {
                this.$(".dms_document_preview .o_preview_directory").remove();
                this.$(".dms_document_preview").prepend(
                    $(
                        QWeb.render("dms.DocumentTreeViewDirectoryPreview", {
                            widget: this,
                            dms_object: node.data,
                        })
                    )
                );
                var self = this;
                var menu = this._loadContextMenu(node);
                _.each(menu, function (action) {
                    self._generateActionButton(node, action, $buttons);
                });
            }
        },
        _generateActionButton: function (node, action, $buttons) {
            if (action.action) {
                var $button = $("<button>", {
                    type: "button",
                    class: "btn btn-secondary " + action.icon,
                    "data-toggle": "dropdown",
                    title: action.label,
                }).on("click", function (event) {
                    event.preventDefault();
                    event.stopPropagation();
                    if (action._disabled && action._disabled()) {
                        return;
                    }
                    action.action();
                });
                $buttons.append($button);
            }
            if (action.submenu) {
                var self = this;
                _.each(action.submenu, function (sub_action) {
                    self._generateActionButton(node, sub_action, $buttons);
                });
            }
        },
        _loadContextMenu: function (node) {
            var menu = {};
            var jstree = this.$tree.jstree(true);
            if (node.data) {
                if (node.data.model === "dms.directory") {
                    menu = this._loadContextMenuDirectoryBefore(jstree, node, menu);
                    menu = this._loadContextMenuBasic(jstree, node, menu);
                    menu = this._loadContextMenuDirectory(jstree, node, menu);
                } else if (node.data.model === "dms.file") {
                    menu = this._loadContextMenuBasic(jstree, node, menu);
                    menu = this._loadContextMenuFile(jstree, node, menu);
                }
            }
            return menu;
        },
        _loadContextMenuBasic: function ($jstree, node, menu) {
            var self = this;
            menu.rename = {
                separator_before: false,
                separator_after: false,
                icon: "fa fa-pencil",
                label: _t("Rename"),
                action: function () {
                    $jstree.edit(node);
                },
                _disabled: function () {
                    return !node.data.data.perm_write || node.data.data.storage;
                },
            };
            menu.action = {
                separator_before: false,
                separator_after: false,
                icon: "fa fa-bolt",
                label: _t("Actions"),
                action: false,
                submenu: {
                    cut: {
                        separator_before: false,
                        separator_after: false,
                        icon: "fa fa-scissors",
                        label: _t("Cut"),
                        action: function () {
                            $jstree.cut(node);
                        },
                        _disabled: function () {
                            return !node.data.data.perm_read || node.data.data.storage;
                        },
                    },
                },
                _disabled: function () {
                    return !node.data.data.perm_read;
                },
            };
            menu.delete = {
                separator_before: false,
                separator_after: false,
                icon: "fa fa-trash-o",
                label: _t("Delete"),
                action: function () {
                    $jstree.delete_node(node);
                },
                _disabled: function () {
                    return !node.data.data.perm_unlink || node.data.data.storage;
                },
            };
            menu.open = {
                separator_before: false,
                separator_after: false,
                icon: "fa fa-external-link",
                label: _t("Open"),
                action: function () {
                    self.trigger_up("dms_open_record", {id: node.id});
                },
            };
            return menu;
        },
        _loadContextMenuDirectoryBefore: function ($jstree, node, menu) {
            var self = this;
            menu.add_directory = {
                separator_before: false,
                separator_after: false,
                icon: "fa fa-folder",
                label: _t("Create directory"),
                action: function () {
                    self._onDMSAddDirectory(node);
                },
                _disabled: function () {
                    return !node.data.data.perm_create;
                },
            };
            menu.add_file = {
                separator_before: false,
                separator_after: true,
                icon: "fa fa-file",
                label: _t("Create File"),
                action: function () {
                    self._onDMSAddFile(node);
                },
                _disabled: function () {
                    return !node.data.data.perm_create;
                },
            };
            return menu;
        },
        _loadContextMenuDirectory: function ($jstree, node, menu) {
            if (menu.action && menu.action.submenu) {
                menu.action.submenu.paste = {
                    separator_before: false,
                    separator_after: false,
                    icon: "fa fa-clipboard",
                    label: _t("Paste"),
                    action: function () {
                        $jstree.paste(node);
                    },
                    _disabled: function () {
                        return !$jstree.can_paste() && !node.data.data.perm_create;
                    },
                };
            }
            return menu;
        },
        _loadContextMenuFile: function ($jstree, node, menu) {
            var self = this;
            menu.preview = {
                separator_before: false,
                separator_after: false,
                icon: "fa fa-eye",
                label: _t("Download"),
                action: function () {
                    self.trigger_up("dms_preview_file", {
                        id: node.id,
                    });
                },
            };
            menu.download = {
                separator_before: false,
                separator_after: false,
                icon: "fa fa-download",
                label: _t("Download"),
                action: function () {
                    framework.blockUI();
                    session.get_file({
                        url: "/web/content",
                        data: {
                            id: node.data.data.id,
                            download: true,
                            field: "content",
                            model: "dms.file",
                            filename_field: "name",
                            filename: node.data.data.filename,
                        },
                        complete: framework.unblockUI,
                        error: () =>
                            self.call("crash_manager", "rpc_error", ...arguments),
                    });
                },
            };
            return menu;
        },
        _onRecordPreview: function (ev) {
            ev.stopPropagation();
            var id = $(ev.currentTarget).data("id");
            if (id) {
                this.trigger_up("dms_preview_file", {
                    id: id,
                    target: ev.target,
                });
            }
        },
        _onOpenRecord: function (ev) {
            ev.stopPropagation();
            var id = $(ev.currentTarget).data("id");
            if (id) {
                this.trigger_up("dms_open_record", {
                    id: id,
                    target: ev.target,
                });
            }
        },
        _onDMSAddDirectory: function (node) {
            var self = this;
            var context = {
                default_parent_directory_id: node.data.res_id,
            };
            new dialogs.FormViewDialog(self, {
                res_model: "dms.directory",
                context: context,
                title: _t("Add Directory: ") + self.string,
                on_saved: function (record, changed) {
                    if (changed) {
                        const selected_id = self.$tree
                            .find(".jstree-clicked")
                            .attr("id");
                        const model_data = self.$tree.jstree(true)._model.data;
                        const state = self.$tree.jstree(true).get_state();
                        const open_res_ids = state.core.open.map(
                            (id) => model_data[id].data.res_id
                        );
                        self.$tree.on("refresh_node.jstree", () => {
                            const model_data_entries = Object.entries(model_data);
                            const ids = model_data_entries
                                .filter(
                                    ([, value]) =>
                                        value.data &&
                                        open_res_ids.includes(value.data.res_id) &&
                                        value.data.model === "dms.directory"
                                )
                                .map((tuple) => tuple[0]);
                            for (var id of ids) {
                                self.$tree.jstree(true).open_node(id);
                            }
                        });
                        self.$tree.jstree(true).refresh_node(selected_id);
                    }
                },
            }).open();
        },
        _onDMSAddFile: function (node) {
            var self = this;
            var context = {
                default_directory_id: node.data.res_id,
            };
            new dialogs.FormViewDialog(self, {
                res_model: "dms.file",
                context: context,
                title: _t("Add File: ") + self.string,
                on_saved: function (record, changed) {
                    if (changed) {
                        const selected_id = self.$tree
                            .find(".jstree-clicked")
                            .attr("id");
                        const model_data = self.$tree.jstree(true)._model.data;
                        const state = self.$tree.jstree(true).get_state();
                        const open_res_ids = state.core.open.map(
                            (id) => model_data[id].data.res_id
                        );
                        self.$tree.on("refresh_node.jstree", () => {
                            const model_data_entries = Object.entries(model_data);
                            const ids = model_data_entries
                                .filter(
                                    ([, value]) =>
                                        value.data &&
                                        open_res_ids.includes(value.data.res_id) &&
                                        value.data.model === "dms.directory"
                                )
                                .map((tuple) => tuple[0]);
                            for (var id of ids) {
                                self.$tree.jstree(true).open_node(id);
                            }
                        });
                        self.$tree.jstree(true).refresh_node(selected_id);
                    }
                },
            }).open();
        },
        _onDMSAddDirectoryRecord: function () {
            var self = this;
            var data = {};
            this.trigger_up("dms_empty_storages", {data: data});
            this._rpc({
                context: {
                    res_id: data.res_id,
                    res_model: data.model,
                },
                model: "dms.field.template",
                method: "create_dms_directory",
            }).then(function () {
                self.trigger_up("reload");
            });
        },
    });

    return DmsTreeRenderer;
});
