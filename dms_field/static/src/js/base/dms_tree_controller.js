odoo.define("dms.DmsTreeController", function(require) {
    "use strict";

    var mixins = require("web.mixins");
    var session = require("web.session");
    var field_utils = require("web.field_utils");

    var mimetype = require("dms_field.mimetype");

    var Domain = require("web.Domain");
    var ServicesMixin = require("web.ServicesMixin");
    var BasicController = require("web.AbstractController");
    var preview = require("dms.preview");
    var FieldPreviewViewer = preview.FieldPreviewViewer;
    var EventDispatcherMixin = mixins.EventDispatcherMixin;
    var dialogs = require("web.view_dialogs");
    var core = require("web.core");
    var _t = core._t;

    var DocumentsController = BasicController.extend(
        EventDispatcherMixin,
        ServicesMixin,
        {
            custom_events: _.extend({}, BasicController.prototype.custom_events, {
                preview_file: "_onPreviewFile",
                load: "_onLoad",
                open_selected_node: "_onOpenSelectedNode",
            }),
            init: function(parent, model, renderer, params) {
                EventDispatcherMixin.init.call(this);
                this.setParent(parent);
                this.setParams(params);
                this._super.apply(this, arguments);
            },
            setParams: function(params) {
                var storage_domain = [];
                var directory_domain = [];
                if (params.modelName === "dms.storage") {
                    storage_domain = [["id", "in", params.initialState.res_ids]];
                    directory_domain = [];
                }
                if (params.modelName === "dms.directory") {
                    storage_domain = [
                        ["storage_directory_ids", "in", params.initialState.res_ids],
                    ];
                    directory_domain = [
                        "|",
                        ["id", "in", params.initialState.res_ids],
                        ["child_directory_ids", "in", params.initialState.res_ids],
                    ];
                }
                this.params = $.extend(
                    true,
                    {},
                    {
                        storage: {
                            domain: storage_domain,
                            context: session.user_context,
                            show: true,
                        },
                        directory: {
                            domain: directory_domain,
                            context: session.user_context,
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
            _onLoad: function(ev) {
                var self = this;
                var node = ev.data.node;
                var params = ev.data.params;
                var args = this._buildArgs(params);
                var result = undefined;
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
                });
            },
            _buildArgs: function(args) {
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
            _buildDomain: function(base, domain) {
                var result = new Domain(base);
                result._addSubdomain(domain || []);
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
                        domain: this._buildDomain(
                            [["storage_id", operator, value]],
                            args.directory.domain
                        ),
                        context: args.directory.context || session.user_context,
                    },
                });
            },
            _loadDirectoriesSingle: function(storage_id, args) {
                return this._loadDirectories("=", storage_id, args);
            },
            _loadDirectoriesMulti: function(storage_ids, args) {
                return this._loadDirectories("in", storage_ids, args);
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
                    domain: this._buildDomain(
                        [["parent_id", operator, value]],
                        args.directory.domain
                    ),
                    context: args.file.context || session.user_context,
                });
            },
            _loadSubdirectoriesSingle: function(directory_id, args) {
                return this._loadSubdirectories("=", directory_id, args);
            },
            _loadSubdirectoriesMulti: function(directory_ids, args) {
                return this._loadSubdirectories("in", directory_ids, args);
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
                    domain: this._buildDomain(
                        [["directory_id", operator, value]],
                        args.file.domain
                    ),
                    context: args.file.context || session.user_context,
                });
            },
            _loadFilesSingle: function(directory_id, args) {
                return this._loadFiles("=", directory_id, args);
            },
            _loadFilesMulti: function(directory_ids, args) {
                return this._loadFiles("in", directory_ids, args);
            },
            _loadInitialData: function(args) {
                var data_loaded = $.Deferred();
                if (args.modelName === "dms.storage") {
                    this._loadStorages(args).then(
                        function(storages) {
                            var loading_data_parts = [];
                            _.each(
                                storages,
                                function(storage, index) {
                                    if (storage.count_storage_directories > 0) {
                                        var directory_loaded = $.Deferred();
                                        loading_data_parts.push(directory_loaded);
                                        this._loadDirectoriesSingle(
                                            storage.id,
                                            args
                                        ).then(function(directories) {
                                            storages[index].directories = directories;
                                            directory_loaded.resolve();
                                        });
                                    }
                                }.bind(this)
                            );
                            $.when.apply($, loading_data_parts).then(
                                function() {
                                    if (args.storage.show) {
                                        var result = _.chain(storages)
                                            .map(
                                                function(storage) {
                                                    var children = _.map(
                                                        storage.directories,
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
                                                return (
                                                    node.children &&
                                                    node.children.length > 0
                                                );
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
                                                                args.file.show
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
                }
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
            _loadNodes: function(nodes, args) {
                var result = $.Deferred();
                var storages_loaded = $.Deferred();
                var directories_loaded = $.Deferred();
                var storage_ids = _.chain(nodes)
                    .filter(function(node) {
                        return node.split("_")[0] === "storage";
                    })
                    .map(function(node) {
                        return parseInt(node.split("_")[1], 10);
                    })
                    .value();
                var directory_ids = _.chain(nodes)
                    .filter(function(node) {
                        return node.split("_")[0] === "directory";
                    })
                    .map(function(node) {
                        return parseInt(node.split("_")[1], 10);
                    })
                    .value();
                if (storage_ids.length > 0) {
                    this._loadDirectoriesMulti(storage_ids, args).then(
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
                            storages_loaded.resolve(directory_nodes);
                        }.bind(this)
                    );
                } else {
                    storages_loaded.resolve([]);
                }
                if (directory_ids.length > 0) {
                    var files_loaded = $.Deferred();
                    var subdirectories_loaded = $.Deferred();
                    this._loadSubdirectoriesMulti(directory_ids, args).then(
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
                            subdirectories_loaded.resolve(directory_nodes);
                        }.bind(this)
                    );
                    if (args.file.show) {
                        this._loadFilesMulti(directory_ids, args).then(
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
                    $.when(subdirectories_loaded, files_loaded).then(function(
                        directories,
                        files
                    ) {
                        directories_loaded.resolve(_.union(directories, files));
                    });
                } else {
                    directories_loaded.resolve([]);
                }
                $.when(storages_loaded, directories_loaded).then(function(
                    storages,
                    directories
                ) {
                    var tree = _.groupBy(_.union(storages, directories), function(
                        item
                    ) {
                        return item.data.parent;
                    });
                    result.resolve(tree);
                });
                return result;
            },
            _searchNodes: function(val, node, args) {
                var result = $.Deferred();
                var files_loaded = $.Deferred();
                var directories_loaded = $.Deferred();
                console.log(node);
                this._searchDirectories(node.data.data.id, val, args).then(function(
                    directories
                ) {
                    var directory_map = _.map(directories, function(directory) {
                        return "directory_" + directory.id;
                    });
                    directories_loaded.resolve(directory_map);
                });
                if (args.directoriesOnly) {
                    files_loaded.resolve([]);
                } else {
                    this._searchFiles(node.data.id, val, args).then(function(files) {
                        files_loaded.resolve(files);
                    });
                }
                $.when(directories_loaded, files_loaded).then(function(
                    directories,
                    files
                ) {
                    result.resolve(_.union(directories, files));
                });
                return result;
            },
            _makeNodeStorage: function(storage, children) {
                var dt = this.model._makeDataPoint({
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
            _makeNodeDirectory: function(directory, showFiles) {
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
                var dt = this.model._makeDataPoint({
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
                        file.permission_create &&
                        (!file.is_locked || file.is_lock_editor),
                    perm_write:
                        file.permission_write &&
                        (!file.is_locked || file.is_lock_editor),
                    perm_unlink:
                        file.permission_unlink &&
                        (!file.is_locked || file.is_lock_editor),
                    thumbnail_link: session.url("/web/image", {
                        model: "dms.file",
                        field: "thumbnail_medium",
                        unique: file.__last_update.replace(/[^0-9]/g, ""),
                        id: file.id,
                    }),
                });
                var dt = this.model._makeDataPoint({
                    data: data,
                    modelName: "dms.file",
                });
                return {
                    id: dt.id,
                    text: dt.data.display_name,
                    icon: mimetype.mimetype2fa(dt.data.mimetype, {prefix: "fa fa-"}),
                    type: "file",
                    data: dt,
                };
            },
            _onPreviewFile: function(ev) {
                var record = this.model.get(ev.data.id, {raw: true});
                console.log(record);
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
                                name: record.name,
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
            _onOpenRecord: function(event) {
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
        }
    );

    return DocumentsController;
});
