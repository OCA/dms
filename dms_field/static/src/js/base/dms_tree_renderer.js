odoo.define("dms.DmsTreeRenderer", function(require) {
    "use strict";

    var BasicRenderer = require("web.BasicRenderer");
    var core = require("web.core");
    var ajax = require("web.ajax");
    var Dialog = require("web.Dialog");

    var crash_manager = require("web.crash_manager");
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
        }),
        template: "dms.DocumentTree",
        init: function(parent, params) {
            this._super.apply(this, arguments);
            this.params = params || {};
            this.config = this._buildTreeConfig();
            this.storage_data = {};
        },

        willStart: function() {
            return $.when(ajax.loadLibs(this), this._super.apply(this, arguments));
        },

        _buildTreeConfig: function() {
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
            var config = {
                core: {
                    widget: this,
                    animation: this.params.animation || 0,
                    multiple: !this.params.disable_multiple,
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
            };
            return config;
        },
        _loadData: function(node, callback) {
            this.trigger_up("load", {
                node: node,
                callback: callback,
            });
        },
        start_tree_triggers: function() {
            var self = this;
            this.$tree.on("open_node.jstree", function(e, data) {
                if (data.node.data && data.node.data.model === "dms.directory") {
                    data.instance.set_icon(data.node, "fa fa-folder-open-o");
                }
            });
            this.$tree.on("close_node.jstree", function(e, data) {
                if (data.node.data && data.node.data.model === "dms.directory") {
                    data.instance.set_icon(data.node, "fa fa-folder-o");
                }
            });
            this.$tree.on("ready.jstree", function(e, data) {
                self.trigger_up("tree_ready", {
                    data: data,
                });
            });
            this.$tree.on("changed.jstree", function(e, data) {
                self.trigger_up("tree_changed", {
                    data: data,
                });
            });
            this.$tree.on("move_node.jstree", function(e, data) {
                self.trigger_up("move_node", {
                    node: data.node,
                    new_parent: data.parent,
                    old_parent: data.old_parent,
                });
            });
            this.$tree.on("copy_node.jstree", function(e, data) {
                self.trigger_up("copy_node", {
                    node: data.node,
                    original: data.original,
                    parent: data.parent,
                });
            });
            this.$tree.on("rename_node.jstree", function(e, data) {
                self.trigger_up("rename_node", {
                    node: data.node,
                    text: data.text,
                    old: data.old,
                });
            });
            this.$tree.on("delete_node.jstree", function(e, data) {
                self.trigger_up("delete_node", {
                    node: data.node,
                    parent: data.parent,
                });
            });
            this.$('[data-toggle="tooltip"]').tooltip();
        },

        _treeChanged: function(ev) {
            var data = ev.data.data;
            if (data.selected && data.selected.length === 1) {
                this._preview_node(data.node);
            }
        },
        start: function() {
            var res = this._super.apply(this, arguments);
            this.$tree = this.$(".dms_tree");
            this.$tree.jstree(this.config);
            this.start_tree_triggers();
            return res;
        },
        _checkCallback: function(operation, node, parent) {
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
            if (operation === "move_node") {
                // Prevent duplicate names
                if (node.data && parent.data) {
                    var names = [];
                    var jstree = this.renderer.$tree.jstree(true);
                    _.each(parent.children, function(child) {
                        var child_node = jstree.get_node(child);
                        if (
                            child_node.data &&
                            child_node.data.model === parent.data.model
                        ) {
                            names.push(child_node.data.name);
                        }
                    });
                    if (names.indexOf(node.data.name) > -1) {
                        return false;
                    }
                }
            }
            return true;
        },
        _checkSelect: function(node) {
            if (this.params.filesOnly && node.data.model !== "dms.file") {
                return false;
            }
            return !(node.parent === "#" && node.data.model === "dms.storage");
        },
        _preview_node: function(node) {
            if (
                node.data &&
                ["dms.directory", "dms.file"].indexOf(node.data.model) !== -1
            ) {
                this.$(".dms_document_preview").html(
                    $(
                        QWeb.render("dms.DocumentTreeViewDirectoryPreview", {
                            widget: this,
                            dms_object: node.data,
                        })
                    )
                );
            }
        },
        _loadContextMenu: function(node) {
            var menu = {};
            var jstree = this.$tree.jstree(true);
            if (node.data) {
                if (node.data.model === "dms.directory") {
                    menu = this._loadContextMenuBasic(jstree, node, menu);
                    menu = this._loadContextMenuDirectory(jstree, node, menu);
                } else if (node.data.model === "dms.file") {
                    menu = this._loadContextMenuBasic(jstree, node, menu);
                    menu = this._loadContextMenuFile(jstree, node, menu);
                }
            }
            return menu;
        },
        _loadContextMenuBasic: function($jstree, node, menu) {
            menu.rename = {
                separator_before: false,
                separator_after: false,
                icon: "fa fa-pencil",
                label: _t("Rename"),
                action: function() {
                    $jstree.edit(node);
                },
                _disabled: function() {
                    return !node.data.perm_write;
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
                        action: function() {
                            $jstree.cut(node);
                        },
                    },
                    copy: {
                        separator_before: false,
                        separator_after: false,
                        icon: "fa fa-clone",
                        label: _t("Copy"),
                        action: function() {
                            $jstree.copy(node);
                        },
                    },
                },
                _disabled: function() {
                    return !node.data.perm_read;
                },
            };
            menu.delete = {
                separator_before: false,
                separator_after: false,
                icon: "fa fa-trash-o",
                label: _t("Delete"),
                action: function() {
                    $jstree.delete_node(node);
                },
                _disabled: function() {
                    return !node.data.perm_unlink;
                },
            };
            return menu;
        },
        _loadContextMenuDirectory: function($jstree, node, menu) {
            if (menu.action && menu.action.submenu) {
                menu.action.submenu.paste = {
                    separator_before: false,
                    separator_after: false,
                    icon: "fa fa-clipboard",
                    label: _t("Paste"),
                    action: function() {
                        $jstree.paste(node);
                    },
                    _disabled: function() {
                        return !$jstree.can_paste() && !node.data.perm_create;
                    },
                };
            }
            return menu;
        },
        _loadContextMenuFile: function($jstree, node, menu) {
            menu.download = {
                separator_before: false,
                separator_after: false,
                icon: "fa fa-download",
                label: _t("Download"),
                action: function() {
                    framework.blockUI();
                    session.get_file({
                        url: "/web/content",
                        data: {
                            id: node.data.odoo_id,
                            download: true,
                            field: "content",
                            model: "dms.file",
                            filename_field: "name",
                            filename: node.data.filename,
                        },
                        complete: framework.unblockUI,
                        error: crash_manager.rpc_error.bind(crash_manager),
                    });
                },
            };
            return menu;
        },
        _show_help: function() {
            var buttons = [
                {
                    text: _t("Ok"),
                    close: true,
                },
            ];
            var dialog = new Dialog(this, {
                size: "medium",
                buttons: buttons,
                $content: $(QWeb.render("dms.DocumentHelpDialogContent")),
                title: _t("Help"),
            });
            dialog.open();
        },
        _onRecordPreview: function(ev) {
            ev.stopPropagation();
            var id = $(ev.currentTarget).data("id");
            if (id) {
                this.trigger_up("preview_file", {
                    id: id,
                    target: ev.target,
                });
            }
        },
        _onOpenRecord: function(ev) {
            ev.stopPropagation();
            var id = $(ev.currentTarget).data("id");
            if (id) {
                this.trigger_up("open_record", {
                    id: id,
                    target: ev.target,
                });
            }
        },
    });

    return DmsTreeRenderer;
});
