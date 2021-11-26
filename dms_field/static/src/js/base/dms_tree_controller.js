odoo.define("dms.DmsTreeController", function(require) {
    "use strict";

    var session = require("web.session");
    var field_utils = require("web.field_utils");

    var mimetype = require("dms_field.mimetype");

    var Domain = require("web.Domain");
    var BasicController = require("web.BasicController");
    var FormController = require("web.FormController");
    var preview = require("mail_preview_base.preview");
    var FieldPreviewViewer = preview.FieldPreviewViewer;
    var dialogs = require("web.view_dialogs");
    var core = require("web.core");
    var _t = core._t;

    var DMSTreeController = {
        init: function(parent, model, renderer, params) {
            this._super.apply(this, arguments);
            this.setParams(params);
        },
        setParams: function(params) {
            var model = params.modelName;
            var storage_domain = [];
            var directory_domain = [];
            var autocompute_directory = false;
            var show_storage = true;
            if (model === "dms.storage") {
                storage_domain = [["id", "in", params.initialState.res_ids]];
                directory_domain = [];
            } else if (model === "dms.directory") {
                storage_domain = [
                    ["storage_directory_ids", "in", params.initialState.res_ids],
                ];
                directory_domain = [
                    "|",
                    ["id", "in", params.initialState.res_ids],
                    ["child_directory_ids", "in", params.initialState.res_ids],
                ];
            } else {
                storage_domain = [["model_ids.model", "=", model]];
                autocompute_directory = true;
                show_storage = false;
            }
            this.params = $.extend(
                true,
                {},
                {
                    storage: {
                        domain: storage_domain,
                        context: session.user_context,
                        show: show_storage,
                    },
                    directory: {
                        domain: directory_domain,
                        context: session.user_context,
                        autocompute_directory: autocompute_directory,
                    },
                    file: {
                        domain: [],
                        context: session.user_context,
                        show: true,
                    },
                    initial: undefined,
                },
                params || {}
            );
        },
        _onDMSLoad: function(ev) {
            var self = this;
            var node = ev.data.node;
            var params = ev.data.params;
            var args = this._buildDMSArgs(params);
            var result = false;
            if (!node || node.id === "#") {
                if (args.initial) {
                    result = $.when(args.initial);
                } else {
                    result = this._loadInitialData(args);
                }
            } else {
                result = this._loadNode(node, args);
            }
            return result.then(function(data) {
                ev.data.callback.call(self.renderer, data);
                if (self.empty_storages.length > 0) {
                    self.renderer.$el
                        .find(".o_dms_add_directory")
                        .removeClass("o_hidden");
                }
            });
        },
        _buildDMSArgs: function(args) {
            return $.extend(
                true,
                {
                    search: {
                        operator: "ilike",
                    },
                },
                this.params,
                args || {}
            );
        },
        _buildDMSDomain: function(base, domain, autocompute_directory) {
            var result = new Domain(base);
            if (autocompute_directory) {
                result._addSubdomain([["res_id", "=", this.renderer.state.res_id]]);
            } else {
                result._addSubdomain(domain || []);
            }
            return result.toArray();
        },
        _loadStorages: function(args) {
            return this._rpc({
                fields: _.union(args.storage.fields || [], [
                    "name",
                    "count_storage_directories",
                ]),
                domain: args.storage.domain || [],
                context: args.storage.context || session.user_context,
                model: "dms.storage",
                method: "search_read",
            });
        },
        _loadDirectories: function(operator, value, args) {
            return this._rpc({
                model: "dms.directory",
                method: "search_read_parents",
                kwargs: {
                    fields: _.union(args.directory.fields || [], [
                        "permission_read",
                        "permission_create",
                        "permission_write",
                        "permission_unlink",
                        "count_directories",
                        "count_files",
                        "name",
                        "parent_id",
                        "__last_update",
                    ]),
                    domain: this._buildDMSDomain(
                        [["storage_id", operator, value]],
                        args.directory.domain,
                        args.directory.autocompute_directory
                    ),
                    context: args.directory.context || session.user_context,
                },
            });
        },
        _loadDirectoriesSingle: function(storage_id, args) {
            return this._loadDirectories("=", storage_id, args);
        },
        _loadSubdirectories: function(operator, value, args) {
            return this._rpc({
                model: "dms.directory",
                method: "search_read",
                fields: _.union(args.directory.fields || [], [
                    "permission_read",
                    "permission_create",
                    "permission_write",
                    "permission_unlink",
                    "count_directories",
                    "count_files",
                    "name",
                    "parent_id",
                    "__last_update",
                ]),
                domain: this._buildDMSDomain(
                    [["parent_id", operator, value]],
                    args.directory.domain,
                    false
                ),
                context: args.file.context || session.user_context,
            });
        },
        _loadSubdirectoriesSingle: function(directory_id, args) {
            return this._loadSubdirectories("=", directory_id, args);
        },
        _loadFiles: function(operator, value, args) {
            return this._rpc({
                model: "dms.file",
                method: "search_read",
                fields: _.union(args.file.fields || [], [
                    "permission_read",
                    "permission_create",
                    "permission_write",
                    "permission_unlink",
                    "name",
                    "res_mimetype",
                    "directory_id",
                    "size",
                    "is_locked",
                    "is_lock_editor",
                    "extension",
                    "__last_update",
                ]),
                domain: this._buildDMSDomain(
                    [["directory_id", operator, value]],
                    args.file.domain
                ),
                context: args.file.context || session.user_context,
            });
        },
        _loadFilesSingle: function(directory_id, args) {
            return this._loadFiles("=", directory_id, args);
        },
        _loadInitialData: function(args) {
            var self = this;
            var data_loaded = $.Deferred();
            this.empty_storages = [];
            this._loadStorages(args).then(
                function(storages) {
                    var loading_data_parts = [];
                    _.each(
                        storages,
                        function(storage, index) {
                            if (storage.count_storage_directories > 0) {
                                var directory_loaded = $.Deferred();
                                loading_data_parts.push(directory_loaded);
                                this._loadDirectoriesSingle(storage.id, args).then(
                                    function(directories) {
                                        if (directories.length > 0) {
                                            storages[index].directories = directories;
                                        } else if (
                                            self.modelName !== "dms.directory" &&
                                            self.modelName !== "dms.storage"
                                        ) {
                                            self.empty_storages.push(storage);
                                        }
                                        directory_loaded.resolve();
                                    }
                                );
                            } else if (
                                self.modelName !== "dms.directory" &&
                                self.modelName !== "dms.storage"
                            ) {
                                self.empty_storages.push(storage);
                            }
                        }.bind(this)
                    );
                    $.when.apply($, loading_data_parts).then(
                        function() {
                            if (args.storage.show) {
                                var result = _.chain(storages)
                                    .map(
                                        function(storage) {
                                            if (!storage.directories) {
                                                return undefined;
                                            }
                                            var children = _.map(
                                                storage.directories || [],
                                                function(directory) {
                                                    return this._makeNodeDirectory(
                                                        directory,
                                                        args.file.show
                                                    );
                                                }.bind(this)
                                            );
                                            return this._makeNodeStorage(
                                                storage,
                                                children
                                            );
                                        }.bind(this)
                                    )
                                    .filter(function(node) {
                                        return node;
                                    })
                                    .value();
                                data_loaded.resolve(result);
                            } else {
                                var nodes = [];
                                _.each(
                                    storages,
                                    function(storage) {
                                        _.each(
                                            storage.directories,
                                            function(directory) {
                                                nodes.push(
                                                    this._makeNodeDirectory(
                                                        directory,
                                                        args.file.show,
                                                        storage
                                                    )
                                                );
                                            }.bind(this)
                                        );
                                    }.bind(this)
                                );
                                data_loaded.resolve(nodes);
                            }
                        }.bind(this)
                    );
                }.bind(this)
            );
            return data_loaded;
        },
        _loadNode: function(node, args) {
            var result = $.Deferred();
            if (node.data && node.data.model === "dms.storage") {
                this._loadDirectoriesSingle(node.data.data.id, args).then(
                    function(directories) {
                        var directory_nodes = _.map(
                            directories,
                            function(directory) {
                                return this._makeNodeDirectory(
                                    directory,
                                    args.file.show
                                );
                            }.bind(this)
                        );
                        result.resolve(directory_nodes);
                    }.bind(this)
                );
            } else if (node.data && node.data.model === "dms.directory") {
                var files_loaded = $.Deferred();
                var directories_loaded = $.Deferred();
                this._loadSubdirectoriesSingle(node.data.data.id, args).then(
                    function(directories) {
                        var directory_nodes = _.map(
                            directories,
                            function(directory) {
                                return this._makeNodeDirectory(
                                    directory,
                                    args.file.show
                                );
                            }.bind(this)
                        );
                        directories_loaded.resolve(directory_nodes);
                    }.bind(this)
                );
                if (args.file.show) {
                    this._loadFilesSingle(node.data.data.id, args).then(
                        function(files) {
                            var file_nodes = _.map(
                                files,
                                function(file) {
                                    return this._makeNodeFile(file);
                                }.bind(this)
                            );
                            files_loaded.resolve(file_nodes);
                        }.bind(this)
                    );
                } else {
                    files_loaded.resolve([]);
                }
                $.when(directories_loaded, files_loaded).then(function(
                    directories,
                    files
                ) {
                    result.resolve(directories.concat(files));
                });
            } else {
                result.resolve([]);
            }
            return result;
        },
        _makeDataPoint: function(dt) {
            return this.model._makeDataPoint(dt);
        },
        _getDataPoint: function(datapointId, attributes) {
            return this.model.get(datapointId, attributes);
        },
        _makeNodeStorage: function(storage, children) {
            var dt = this._makeDataPoint({
                data: storage,
                modelName: "dms.storage",
            });
            return {
                id: "storage_" + storage.id,
                text: storage.name,
                icon: "fa fa-database",
                type: "storage",
                data: dt,
                children: children,
            };
        },
        _makeNodeDirectory: function(directory, showFiles, storage) {
            var data = _.extend(directory, {
                name: directory.name,
                perm_read: directory.permission_read,
                perm_create: directory.permission_create,
                perm_write: directory.permission_write,
                perm_unlink: directory.permission_unlink,

                thumbnail_link: session.url("/web/image", {
                    model: "dms.directory",
                    field: "thumbnail_medium",
                    unique: directory.__last_update.replace(/[^0-9]/g, ""),
                    id: directory.id,
                }),
            });
            if (
                storage &&
                this.modelName !== "dms.directory" &&
                this.modelName !== "dms.storage"
            ) {
                // We are assuming this is a record directory, so disabling actions
                data.name = storage.name;
                data.storage = true;
            }
            var dt = this._makeDataPoint({
                data: data,
                modelName: "dms.directory",
            });
            dt.parent = directory.parent_id
                ? "directory_" + directory.parent_id[0]
                : "#";
            var directoryNode = {
                id: "directory_" + directory.id,
                text: directory.name,
                icon: "fa fa-folder-o",
                type: "directory",
                data: dt,
            };
            if (showFiles) {
                directoryNode.children =
                    directory.count_directories + directory.count_files > 0;
            } else {
                directoryNode.children = directory.count_directories > 0;
            }
            return directoryNode;
        },
        _makeNodeFile: function(file) {
            var data = _.extend(file, {
                filename: file.name,
                display_name: file.name,
                binary_size: field_utils.format.binary_size(file.size),
                perm_read: file.permission_read,
                perm_create:
                    file.permission_create && (!file.is_locked || file.is_lock_editor),
                perm_write:
                    file.permission_write && (!file.is_locked || file.is_lock_editor),
                perm_unlink:
                    file.permission_unlink && (!file.is_locked || file.is_lock_editor),
                thumbnail_link: session.url("/web/image", {
                    model: "dms.file",
                    field: "thumbnail_medium",
                    unique: file.__last_update.replace(/[^0-9]/g, ""),
                    id: file.id,
                }),
            });
            var dt = this._makeDataPoint({
                data: data,
                modelName: "dms.file",
            });
            return {
                id: dt.id,
                text: dt.data.display_name,
                icon: mimetype.mimetype2fa(dt.data.res_mimetype, {prefix: "fa fa-"}),
                type: "file",
                data: dt,
            };
        },
        _onDMSPreviewFile: function(ev) {
            var record = this._getDataPoint(ev.data.id, {raw: true});
            var fieldName = "content";
            var file_mimetype = record.data.res_mimetype;
            var type = file_mimetype.split("/").shift();
            if (
                type === "video" ||
                type === "image" ||
                file_mimetype === "application/pdf"
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
                    record.model,
                    fieldName
                );
                attachmentViewer.appendTo($("body"));
            } else {
                window.location =
                    "/web/content/" +
                    record.model +
                    "/" +
                    record.data.id +
                    "/" +
                    fieldName +
                    "/" +
                    record.data.name +
                    "?download=true";
            }
        },
        _onDMSOpenRecord: function(event) {
            event.stopPropagation();
            var self = this;
            var record = this.model.get(event.data.id, {raw: true});
            new dialogs.FormViewDialog(self, {
                context: event.data.context,
                fields_view: event.data.fields_view,
                on_saved: event.data.on_saved,
                on_remove: event.data.on_remove,
                readonly: event.data.readonly,
                deletable: event.data.deletable,
                res_id: record.res_id,
                res_model: record.model,
                title: _t("Open: ") + event.data.string,
            }).open();
        },
        _onDMSEmptyStorages: function(event) {
            event.data.data.model = this.modelName;
            event.data.data.empty_storages = this.empty_storages;
            event.data.data.res_id = this.renderer.state.res_id;
        },
        _onDMSRenameNode: function(event) {
            var record = this._getDataPoint(event.data.node.data.id, {raw: true});
            record.data.name = event.data.text;
            event.data.node.data = record;
            return this._rpc({
                model: event.data.node.data.model,
                method: "write",
                args: [
                    [event.data.node.data.res_id],
                    {
                        name: event.data.text,
                    },
                ],
            });
        },
        _onDMSDeleteNode: function(event) {
            return this._rpc({
                model: event.data.node.data.model,
                method: "unlink",
                args: [[event.data.node.data.res_id]],
            });
        },
        _onDMSMoveNode: function(event) {
            var data = {};
            if (event.data.node.data.model === "dms.file") {
                data.directory_id = event.data.new_parent.data.res_id;
            } else if (event.data.node.data.model === "dms.directory") {
                data.parent_id = event.data.new_parent.data.res_id;
            }
            return this._rpc({
                model: event.data.node.data.model,
                method: "write",
                args: [[event.data.node.data.res_id], data],
            });
        },
    };

    var custom_events = {
        dms_preview_file: "_onDMSPreviewFile",
        dms_load: "_onDMSLoad",
        dms_open_record: "_onDMSOpenRecord",
        dms_empty_storages: "_onDMSEmptyStorages",
        dms_rename_node: "_onDMSRenameNode",
        dms_delete_node: "_onDMSDeleteNode",
        dms_move_node: "_onDMSMoveNode",
    };

    FormController.include(
        _.extend(DMSTreeController, {
            custom_events: _.extend(
                {},
                FormController.prototype.custom_events,
                custom_events
            ),
        })
    );

    return {
        Controller: BasicController.extend(
            _.extend(DMSTreeController, {
                custom_events: _.extend(
                    {},
                    BasicController.prototype.custom_events,
                    custom_events
                ),
            })
        ),
        custom_events: custom_events,
        DMSTreeController: DMSTreeController,
    };
});
