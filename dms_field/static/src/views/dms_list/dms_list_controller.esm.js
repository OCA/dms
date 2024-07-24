/** @odoo-module */
/* Copyright 2024 Tecnativa - Carlos Roca
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl). */

import {Layout} from "@web/search/layout";
import {useService} from "@web/core/utils/hooks";
import {useModel} from "@web/views/model";
const {Component, onRendered} = owl;
import {session} from "@web/session";
import {Deferred} from "@web/core/utils/concurrency";
import {Domain} from "@web/core/domain";
import {mimetype2fa} from "../../utils/mimetype.esm";
import {formatBinarySize} from "../../utils/format_binary_size.esm";
import {patch} from "@web/core/utils/patch";
import {DynamicRecordList} from "@web/views/relational_model";

export const DMSListControllerObject = {
    setup() {
        this._super(...arguments);
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.http = useService("http");
        const {rootState} = this.props.state || {};
        this.model =
            (this.props.record && this.props.record.model) ||
            useModel(this.props.Model, {
                resModel: this.props.resModel,
                fields: this.props.fields,
                activeFields: this.props.archInfo.activeFields,
                viewMode: "dms_list",
                rootState,
            });
        this.resModel = this.props.resModel || this.props.record.resModel;
        this.rendererActions = {
            onDMSCreateEmptyStorages: this.onDMSCreateEmptyStorages.bind(this),
            onDMSLoad: this.onDMSLoad.bind(this),
            onDMSRenameNode: this.onDMSRenameNode.bind(this),
            onDMSMoveNode: this.onDMSMoveNode.bind(this),
            onDMSDeleteNode: this.onDMSDeleteNode.bind(this),
            onDMSDroppedFile: this.onDMSDroppedFile.bind(this),
        };
        onRendered(() => {
            this.processProps();
        });
    },
    sanitizeDMSModel(model) {
        return model;
    },
    processProps() {
        const model = this.sanitizeDMSModel(this.resModel);
        var storage_domain = [];
        var directory_domain = [];
        var autocompute_directory = false;
        var show_storage = true;
        if (model === "dms.storage") {
            if (this.model.root.data && this.model.root.data.id) {
                storage_domain = [["id", "=", this.model.root.data.id]];
            } else {
                storage_domain = [
                    [
                        "id",
                        "in",
                        this.model.root.records.map((record) => {
                            return record.resId;
                        }),
                    ],
                ];
            }
            directory_domain = [];
        } else if (model === "dms.field.template") {
            if (this.model.root.resId) {
                storage_domain = [["id", "=", this.model.root.data.storage_id[0]]];
            } else {
                storage_domain = [["id", "=", 0]];
            }
            directory_domain = [
                [
                    "root_directory_id",
                    "in",
                    this.model.root.data.dms_directory_ids.records.map((record) => {
                        return record.resId;
                    }),
                ],
            ];
        } else {
            storage_domain = [["field_template_ids.model", "=", model]];
            autocompute_directory = true;
            show_storage = false;
        }
        this.params = {
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
        };
    },
    async onDMSLoad(node) {
        await this.model.root.load();
        this.model.notify();
        this.processProps();
        var args = this.buildDMSArgs();
        var result = false;
        if (!node || node.id === "#") {
            result = this.loadInitialData(args);
        } else {
            result = this.loadNode(node, args);
        }
        return {result, empty_storages: this.empty_storages};
    },
    loadInitialData(args) {
        var self = this;
        var data_loaded = new Deferred();
        this.empty_storages = [];
        this.loadStorages(args).then(
            function (storages) {
                var loading_data_parts = [];
                _.each(
                    storages,
                    function (storage, index) {
                        if (storage.count_storage_directories > 0) {
                            var directory_loaded = new Deferred();
                            loading_data_parts.push(directory_loaded);
                            this.loadDirectoriesSingle(storage.id, args).then(function (
                                directories
                            ) {
                                if (directories.length > 0) {
                                    storages[index].directories = directories;
                                } else if (
                                    self.props.resModel !== "dms.directory" &&
                                    self.props.resModel !== "dms.storage"
                                ) {
                                    self.empty_storages.push(storage);
                                }
                                directory_loaded.resolve();
                            });
                        } else if (
                            self.props.resModel !== "dms.directory" &&
                            self.props.resModel !== "dms.storage"
                        ) {
                            self.empty_storages.push(storage);
                        }
                    }.bind(this)
                );
                $.when.apply($, loading_data_parts).then(
                    function () {
                        if (args.storage.show) {
                            var result = _.chain(storages)
                                .map(
                                    function (storage) {
                                        if (!storage.directories) {
                                            return undefined;
                                        }
                                        var children = _.map(
                                            storage.directories || [],
                                            function (directory) {
                                                return this.makeNodeDirectory(
                                                    directory,
                                                    args.file.show
                                                );
                                            }.bind(this)
                                        );
                                        return this.makeNodeStorage(storage, children);
                                    }.bind(this)
                                )
                                .filter(function (node) {
                                    return node;
                                })
                                .value();
                            data_loaded.resolve(result);
                        } else {
                            var nodes = [];
                            _.each(
                                storages,
                                function (storage) {
                                    _.each(
                                        storage.directories,
                                        function (directory) {
                                            nodes.push(
                                                this.makeNodeDirectory(
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
                // Launch _update_overlay to show the drag and drop
                // this._update_overlay();
            }.bind(this)
        );
        return data_loaded;
    },
    loadNode(node, args) {
        var result = new Deferred();
        if (node.data && node.data.resModel === "dms.storage") {
            this.loadDirectoriesSingle(node.data.data.id, args).then(
                function (directories) {
                    var directory_nodes = _.map(
                        directories,
                        function (directory) {
                            return this.makeNodeDirectory(directory, args.file.show);
                        }.bind(this)
                    );
                    result.resolve(directory_nodes);
                }.bind(this)
            );
        } else if (node.data && node.data.resModel === "dms.directory") {
            var files_loaded = new Deferred();
            var directories_loaded = new Deferred();
            this.loadSubdirectoriesSingle(node.data.data.id, args).then(
                function (directories) {
                    var directory_nodes = _.map(
                        directories,
                        function (directory) {
                            return this.makeNodeDirectory(directory, args.file.show);
                        }.bind(this)
                    );
                    directories_loaded.resolve(directory_nodes);
                }.bind(this)
            );
            if (args.file.show) {
                this.loadFilesSingle(node.data.data.id, args).then(
                    function (files) {
                        var file_nodes = _.map(
                            files,
                            function (file) {
                                return this.makeNodeFile(file);
                            }.bind(this)
                        );
                        files_loaded.resolve(file_nodes);
                    }.bind(this)
                );
            } else {
                files_loaded.resolve([]);
            }
            $.when(directories_loaded, files_loaded).then(function (
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
    makeNodeDirectory(directory, showFiles, storage) {
        var data = _.extend(directory, {
            name: directory.name,
            perm_read: directory.permission_read,
            perm_create: directory.permission_create,
            perm_write: directory.permission_write,
            perm_unlink: directory.permission_unlink,
            icon_url: directory.icon_url,
            count_total_directories: directory.count_total_directories,
            count_total_files: directory.count_total_files,
            human_size: directory.human_size,
            count_elements: directory.count_elements,
        });
        if (
            storage &&
            this.resModel !== "dms.directory" &&
            this.resModel !== "dms.storage"
        ) {
            // We are assuming this is a record directory, so disabling actions
            data.name = storage.name;
            data.storage = true;
        }
        var dt = this.makeDataPoint({
            data: data,
            resModel: "dms.directory",
        });
        dt.parent = directory.parent_id ? "directory_" + directory.parent_id[0] : "#";
        var directoryNode = {
            id: dt.id,
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
    makeNodeFile(file) {
        var data = _.extend(file, {
            filename: file.name,
            display_name: file.name,
            binary_size: formatBinarySize(file.size),
            perm_read: file.permission_read,
            perm_create:
                file.permission_create && (!file.is_locked || file.is_lock_editor),
            perm_write:
                file.permission_write && (!file.is_locked || file.is_lock_editor),
            perm_unlink:
                file.permission_unlink && (!file.is_locked || file.is_lock_editor),
            icon_url: file.icon_url,
        });
        var dt = this.makeDataPoint({
            data: data,
            resModel: "dms.file",
        });
        return {
            id: dt.id,
            text: dt.data.display_name,
            icon: mimetype2fa(dt.data.mimetype, {prefix: "fa fa-"}),
            type: "file",
            data: dt,
        };
    },
    makeNodeStorage(storage, children) {
        var dt = this.makeDataPoint({
            data: storage,
            resModel: "dms.storage",
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
    makeDataPoint(dt) {
        return new DynamicRecordList(this.model, dt);
    },
    loadDirectories(operator, value, args) {
        return this.orm.call("dms.directory", "search_read_parents", [], {
            fields: _.union(args.directory.fields || [], [
                "permission_read",
                "permission_create",
                "permission_write",
                "permission_unlink",
                "count_directories",
                "count_files",
                "name",
                "parent_id",
                "icon_url",
                "count_total_directories",
                "count_total_files",
                "human_size",
                "count_elements",
                "__last_update",
            ]),
            domain: this.buildDMSDomain(
                [["storage_id", operator, value]],
                args.directory.domain,
                args.directory.autocompute_directory
            ),
            context: args.directory.context || session.user_context,
        });
    },
    loadDirectoriesSingle(storage_id, args) {
        return this.loadDirectories("=", storage_id, args);
    },
    loadSubdirectories(operator, value, args) {
        const domain = this.buildDMSDomain(
            [["parent_id", operator, value]],
            args.directory.domain,
            false
        );
        const fields = _.union(args.directory.fields || [], [
            "permission_read",
            "permission_create",
            "permission_write",
            "permission_unlink",
            "count_directories",
            "count_files",
            "name",
            "parent_id",
            "icon_url",
            "count_total_directories",
            "count_total_files",
            "human_size",
            "count_elements",
            "__last_update",
        ]);
        return this.orm.searchRead("dms.directory", domain, fields, {
            context: args.file.context || session.user_context,
        });
    },
    loadSubdirectoriesSingle(directory_id, args) {
        return this.loadSubdirectories("=", directory_id, args);
    },
    loadFiles(operator, value, args) {
        const domain = this.buildDMSDomain(
            [["directory_id", operator, value]],
            args.file.domain
        );
        const fields = _.union(args.file.fields || [], [
            "permission_read",
            "permission_create",
            "permission_write",
            "permission_unlink",
            "icon_url",
            "name",
            "mimetype",
            "directory_id",
            "human_size",
            "is_locked",
            "is_lock_editor",
            "extension",
            "__last_update",
        ]);
        return this.orm.searchRead("dms.file", domain, fields, {
            context: args.file.context || session.user_context,
        });
    },
    loadFilesSingle(directory_id, args) {
        return this.loadFiles("=", directory_id, args);
    },
    loadStorages(args) {
        const fields = _.union(args.storage.fields || [], [
            "name",
            "count_storage_directories",
        ]);
        return this.orm.searchRead("dms.storage", args.storage.domain || [], fields, {
            context: args.storage.context || session.user_context,
        });
    },
    buildDMSDomain(base, domain, autocompute_directory) {
        var result = new Domain(base);
        if (autocompute_directory) {
            result = Domain.and([
                result,
                new Domain([["res_id", "=", this.model.root.resId]]),
            ]);
        } else {
            result = Domain.and([result, new Domain(domain || [])]);
        }
        return result.toList();
    },
    buildDMSArgs() {
        return {
            ...this.params,
            search: {
                operator: "ilike",
            },
        };
    },
    onDMSCreateEmptyStorages() {
        var data = {
            model: this.resModel,
            empty_storages: this.empty_storages,
            res_id: this.props.record.resId,
        };
        return this.orm.call("dms.field.template", "create_dms_directory", [], {
            context: {
                res_id: data.res_id,
                res_model: data.model,
            },
        });
    },
    onDMSRenameNode(node, text) {
        node.data.data.name = text;
        return this.orm.write(node.data.resModel, [node.data.data.id], {
            name: text,
        });
    },
    onDMSMoveNode(node, newParent) {
        var data = {};
        if (node.data.resModel === "dms.file") {
            data.directory_id = newParent.data.data.id;
        } else if (node.data.resModel === "dms.directory") {
            data.parent_id = newParent.data.data.id;
        }
        return this.orm.write(node.data.resModel, [node.data.data.id], data);
    },
    onDMSDeleteNode(node) {
        return this.orm.unlink(node.data.resModel, [node.data.data.id]);
    },
    async onDMSDroppedFile(directoryId, files) {
        const params = {
            csrf_token: odoo.csrf_token,
            ufile: [...files],
            model: "dms.file",
            id: 0,
        };
        const fileData = await this.http.post(
            "/web/binary/upload_attachment",
            params,
            "text"
        );
        const attachments = JSON.parse(fileData);
        if (attachments.error) {
            throw new Error(attachments.error);
        }
        const attachmentIds = attachments.map((a) => a.id);
        const ctx = this.props.context || this.props.record.context;
        if (!attachmentIds.length) {
            return "no_attachments";
        }
        ctx.default_directory_id = directoryId;
        const attachment_datas = await this.orm.call(
            "dms.file",
            "get_dms_files_from_attachments",
            ["", attachmentIds]
        );
        const attachments_args = [];
        attachment_datas.forEach((attachment_data) => {
            attachments_args.push({
                name: attachment_data.name,
                content: attachment_data.datas,
                mimetype: attachment_data.mimetype,
            });
        });
        return this.orm.call("dms.file", "create", [attachments_args], {
            context: ctx,
        });
    },
};

export class DmsListController extends Component {}
patch(DmsListController.prototype, "DmsListControllerPatch", DMSListControllerObject);
DmsListController.template = "dms_field.View";
DmsListController.components = {Layout};
