/* Copyright 2024 Tecnativa - Carlos Roca
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl). */

import {Component, t, useProps} from "@odoo/owl";
import {DEFAULT_MAX_FILE_SIZE} from "@web/core/utils/files";
import {Domain} from "@web/core/domain";
import {Layout} from "@web/search/layout";
import {_t} from "@web/core/l10n/translation";
import {extractFieldsFromArchInfo} from "@web/model/relational_model/utils";
import {formatBinarySize} from "../../utils/format_binary_size.esm";
import {patch} from "@web/core/utils/patch";
import {session} from "@web/session";
import {standardViewProps} from "@web/views/standard_view_props";
import {useModelWithSampleData} from "@web/model/model";
import {useService} from "@web/core/utils/hooks";
import {user} from "@web/core/user";

const DIRECTORY_FIELDS = [
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
    "write_date",
];

const FILE_FIELDS = [
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
    "write_date",
];

/**
 * Logic shared by the dms_list view controller and the x2many field (used with
 * mode="dms_list"). It loads the DMS records and builds the nodes of the tree.
 *
 * @returns {Object} object to patch the component prototype with
 */
export function getDMSListControllerObject() {
    return {
        setup() {
            super.setup(...arguments);
            this.orm = useService("orm");
            this.actionService = useService("action");
            this.http = useService("http");
            this.model =
                (this.props.record && this.props.record.model) ||
                useModelWithSampleData(this.props.Model, this.modelParams());
            this.resModel = this.props.resModel || this.props.record.resModel;
            this.empty_storages = [];
            this.rendererActions = {
                onDMSCreateEmptyStorages: this.onDMSCreateEmptyStorages.bind(this),
                onDMSLoad: this.onDMSLoad.bind(this),
                onDMSRenameNode: this.onDMSRenameNode.bind(this),
                onDMSMoveNode: this.onDMSMoveNode.bind(this),
                onDMSDeleteNode: this.onDMSDeleteNode.bind(this),
                onDMSDroppedFile: this.onDMSDroppedFile.bind(this),
            };
        },
        modelParams() {
            const {activeFields, fields} = extractFieldsFromArchInfo(
                this.props.archInfo,
                this.props.fields
            );
            const modelConfig = this.props.state?.modelState?.config || {
                resModel: this.props.resModel,
                fields,
                activeFields,
            };
            return {
                config: modelConfig,
                state: this.props.state?.modelState,
            };
        },
        sanitizeDMSModel(model) {
            return model;
        },
        processProps() {
            const model = this.sanitizeDMSModel(this.resModel);
            let storage_domain = [];
            let directory_domain = [];
            let autocompute_directory = false;
            let show_storage = true;
            if (model === "dms.storage") {
                if (this.model.root.resId) {
                    storage_domain = [["id", "=", this.model.root.resId]];
                } else {
                    storage_domain = [
                        [
                            "id",
                            "in",
                            this.model.root.records.map((record) => record.resId),
                        ],
                    ];
                }
            } else if (model === "dms.field.template") {
                if (this.model.root.resId) {
                    storage_domain = [["id", "=", this.model.root.data.storage_id.id]];
                } else {
                    storage_domain = [["id", "=", 0]];
                }
                directory_domain = [
                    [
                        "root_directory_id",
                        "in",
                        this.model.root.data.dms_directory_ids.records.map(
                            (record) => record.resId
                        ),
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
                    context: user.context,
                    show: show_storage,
                },
                directory: {
                    domain: directory_domain,
                    context: user.context,
                    autocompute_directory: autocompute_directory,
                },
                file: {
                    domain: [],
                    context: user.context,
                    show: true,
                },
            };
        },
        /**
         * @param {Object|null} node the node to load the children of, or null
         *  to load the root nodes.
         * @returns {Promise<{result: Object[], empty_storages: Object[]}>}
         */
        async onDMSLoad(node) {
            this.processProps();
            const args = this.buildDMSArgs();
            let result = [];
            if (!node || node.id === "#") {
                result = await this.loadInitialData(args);
            } else {
                result = await this.loadNode(node, args);
            }
            return {result, empty_storages: this.empty_storages};
        },
        async loadInitialData(args) {
            const storages = await this.loadStorages(args);
            const isRecordView =
                this.resModel !== "dms.directory" && this.resModel !== "dms.storage";
            this.empty_storages = [];
            await Promise.all(
                storages.map(async (storage) => {
                    if (storage.count_storage_directories > 0) {
                        const directories = await this.loadDirectoriesSingle(
                            storage.id,
                            args
                        );
                        if (directories.length > 0) {
                            storage.directories = directories;
                            return;
                        }
                    }
                    if (isRecordView) {
                        this.empty_storages.push(storage);
                    }
                })
            );
            if (args.storage.show) {
                return storages
                    .filter((storage) => storage.directories)
                    .map((storage) =>
                        this.makeNodeStorage(
                            storage,
                            storage.directories.map((directory) =>
                                this.makeNodeDirectory(directory, args.file.show)
                            )
                        )
                    );
            }
            return storages.flatMap((storage) =>
                (storage.directories || []).map((directory) =>
                    this.makeNodeDirectory(directory, args.file.show, storage)
                )
            );
        },
        async loadNode(node, args) {
            const resModel = node.data?.resModel;
            if (resModel === "dms.storage") {
                const directories = await this.loadDirectoriesSingle(
                    node.data.data.id,
                    args
                );
                return directories.map((directory) =>
                    this.makeNodeDirectory(directory, args.file.show)
                );
            } else if (resModel === "dms.directory") {
                const [directories, files] = await Promise.all([
                    this.loadSubdirectoriesSingle(node.data.data.id, args),
                    args.file.show
                        ? this.loadFilesSingle(node.data.data.id, args)
                        : Promise.resolve([]),
                ]);
                return [
                    ...directories.map((directory) =>
                        this.makeNodeDirectory(directory, args.file.show)
                    ),
                    ...files.map((file) => this.makeNodeFile(file)),
                ];
            }
            return [];
        },
        makeNodeDirectory(directory, showFiles, storage) {
            const data = Object.assign(directory, {
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
            let text = directory.name;
            if (
                storage &&
                this.resModel !== "dms.directory" &&
                this.resModel !== "dms.storage"
            ) {
                // We are assuming this is a record directory, so disabling actions
                data.name = storage.name;
                data.storage = true;
                text = storage.name;
            }
            const count = showFiles
                ? directory.count_directories + directory.count_files
                : directory.count_directories;
            return {
                id: `dms.directory_${directory.id}`,
                text,
                type: "directory",
                data: {data, resModel: "dms.directory"},
                children: count > 0,
            };
        },
        makeNodeFile(file) {
            const canEdit = !file.is_locked || file.is_lock_editor;
            const data = {
                ...file,
                filename: file.name,
                display_name: file.name,
                binary_size: formatBinarySize(file.size),
                perm_read: file.permission_read,
                perm_create: file.permission_create && canEdit,
                perm_write: file.permission_write && canEdit,
                perm_unlink: file.permission_unlink && canEdit,
                icon_url: file.icon_url,
            };
            return {
                id: `dms.file_${file.id}`,
                text: data.display_name,
                type: "file",
                data: {data, resModel: "dms.file"},
                children: false,
            };
        },
        makeNodeStorage(storage, children) {
            return {
                id: `dms.storage_${storage.id}`,
                text: storage.name,
                type: "storage",
                data: {data: storage, resModel: "dms.storage"},
                children,
            };
        },
        loadDirectories(operator, value, args) {
            return this.orm.call("dms.directory", "search_read_parents", [], {
                fields: [
                    ...new Set([...(args.directory.fields || []), ...DIRECTORY_FIELDS]),
                ],
                domain: this.buildDMSDomain(
                    [["storage_id", operator, value]],
                    args.directory.domain,
                    args.directory.autocompute_directory
                ),
                context: args.directory.context || user.context,
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
            const fields = [
                ...new Set([...(args.directory.fields || []), ...DIRECTORY_FIELDS]),
            ];
            return this.orm.searchRead("dms.directory", domain, fields, {
                context: args.directory.context || user.context,
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
            const fields = [...new Set([...(args.file.fields || []), ...FILE_FIELDS])];
            return this.orm.searchRead("dms.file", domain, fields, {
                context: args.file.context || user.context,
            });
        },
        loadFilesSingle(directory_id, args) {
            return this.loadFiles("=", directory_id, args);
        },
        loadStorages(args) {
            const fields = [
                ...new Set([
                    ...(args.storage.fields || []),
                    "name",
                    "count_storage_directories",
                ]),
            ];
            return this.orm.searchRead(
                "dms.storage",
                args.storage.domain || [],
                fields,
                {
                    context: args.storage.context || user.context,
                }
            );
        },
        buildDMSDomain(base, domain, autocompute_directory) {
            let result = new Domain(base);
            if (autocompute_directory) {
                result = Domain.and([
                    result,
                    new Domain([
                        ["res_id", "=", this.model.root.resId],
                        ["res_model", "=", this.sanitizeDMSModel(this.resModel)],
                    ]),
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
            return this.orm.call("dms.field.template", "create_dms_directory", [], {
                context: {
                    res_id: this.props.record.resId,
                    res_model: this.sanitizeDMSModel(this.resModel),
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
            const data = {};
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
        /**
         * @param {Number} directoryId
         * @param {FileList} files
         * @returns {Promise<{ids: Number[], errors: String[]}>} the ids of the
         *  created dms.file records and the errors of the failed uploads.
         */
        async onDMSDroppedFile(directoryId, files) {
            const maxSize = session.max_file_upload_size || DEFAULT_MAX_FILE_SIZE;
            const ids = [];
            const errors = [];
            // One request per file, as the size limit of the server applies to
            // the whole request
            const tooLargeError = (file) =>
                _t(
                    "The file “%(name)s” is too large to be uploaded. The maximum allowed size is %(maxSize)s.",
                    {name: file.name, maxSize: formatBinarySize(maxSize)}
                );
            for (const file of files) {
                if (file.size > maxSize) {
                    errors.push(tooLargeError(file));
                    continue;
                }
                let results = [];
                try {
                    results = await this.uploadDMSFile(directoryId, file);
                } catch (error) {
                    // The request (file and form data) exceeds the server limit
                    if (error.message === "Content too large") {
                        errors.push(tooLargeError(file));
                    } else {
                        errors.push(
                            _t("The file “%(name)s” could not be uploaded: %(error)s", {
                                name: file.name,
                                error: error.message,
                            })
                        );
                    }
                    continue;
                }
                for (const result of results) {
                    if (result.id) {
                        ids.push(result.id);
                    } else if (result.error) {
                        errors.push(result.error);
                    }
                }
            }
            return {ids, errors};
        },
        /**
         * @param {Number} directoryId
         * @param {File} file
         * @returns {Promise<Object[]>} [{id}] or [{error}]
         */
        async uploadDMSFile(directoryId, file) {
            const fileData = await this.http.post(
                "/web/binary/upload_dms_file",
                {
                    csrf_token: odoo.csrf_token,
                    ufile: [file],
                    directory_id: directoryId,
                },
                "text"
            );
            return JSON.parse(fileData);
        },
    };
}

export class DmsListController extends Component {
    static template = "dms_field.View";
    static components = {Layout};

    props = useProps({
        ...standardViewProps,
        Model: t.function(),
        Renderer: t.function(),
        archInfo: t.object(),
    });
}
patch(DmsListController.prototype, getDMSListControllerObject());
