/** @odoo-module */
/* Copyright 2024 Tecnativa - Carlos Roca
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl). */

import {_lt} from "@web/core/l10n/translation";
import {useService} from "@web/core/utils/hooks";
import {loadCSS, loadJS} from "@web/core/assets";
const {Component, onMounted, onWillStart, useEffect, useRef, useState} = owl;
import {download} from "@web/core/network/download";
import {FormViewDialog} from "@web/views/view_dialogs/form_view_dialog";

export class DmsListRenderer extends Component {
    setup() {
        this.js_tree = useRef("jstree");
        this.extra_actions = useRef("extra_actions");
        this.dms_add_directory = useRef("dms_add_directory");
        this.nodeSelectedState = useState({data: {}});
        this.messaging = useService("messaging");
        this.notification = useService("notification");
        this.dialog = useService("dialog");
        this.dragState = useState({
            showDragZone: false,
        });
        this.dropZone = useRef("dropZone");

        useEffect(
            (el) => {
                if (!el) {
                    return;
                }
                const highlight = this.highlight.bind(this);
                const unhighlight = this.unhighlight.bind(this);
                const drop = this.onDrop.bind(this);
                el.addEventListener("dragover", highlight);
                el.addEventListener("dragleave", unhighlight);
                el.addEventListener("drop", drop);
                return () => {
                    el.removeEventListener("dragover", highlight);
                    el.removeEventListener("dragleave", unhighlight);
                    el.removeEventListener("drop", drop);
                };
            },

            () => [this.dropZone.el]
        );
        onWillStart(async () => {
            await loadJS("/dms_field/static/lib/jsTree/jstree.js");
            await loadCSS("/dms_field/static/lib/jsTree/themes/proton/style.css");
            this.config = this.buildTreeConfig();
        });
        onMounted(() => {
            this.$tree = $(this.js_tree.el);
            this.$tree.jstree(this.config);
            this.startTreeTriggers();
        });
    }
    buildTreeConfig() {
        var plugins = [
            "conditionalselect",
            "massload",
            "wholerow",
            "state",
            "sort",
            "search",
            "types",
            "contextmenu",
        ];
        return {
            core: {
                widget: this,
                animation: 0,
                multiple: false,
                check_callback: this.checkCallback.bind(this),
                themes: {
                    name: "proton",
                    responsive: true,
                },
                data: this.loadData.bind(this),
            },
            contextmenu: {
                items: this.loadContextMenu.bind(this),
            },
            state: {
                key: "documents",
            },
            conditionalselect: this.checkSelect.bind(this),
            plugins: plugins,
            sort: function (a, b) {
                // Correctly sort the records according to the type of element
                // (folder or file).
                // Do not use node.icon because they may have (or will have) a
                // different icon for each file according to its extension.
                var node_a = this.get_node(a);
                var node_b = this.get_node(b);
                if (node_a.data.resModel === node_b.data.resModel) {
                    return node_a.text > node_b.text ? 1 : -1;
                }
                return node_a.data.resModel > node_b.data.resModel ? 1 : -1;
            },
        };
    }
    startTreeTriggers() {
        this.$tree.on("open_node.jstree", (e, data) => {
            if (data.node.data && data.node.data.resModel === "dms.directory") {
                data.instance.set_icon(data.node, "fa fa-folder-open-o");
            }
        });
        this.$tree.on("close_node.jstree", (e, data) => {
            if (data.node.data && data.node.data.resModel === "dms.directory") {
                data.instance.set_icon(data.node, "fa fa-folder-o");
            }
        });
        this.$tree.on("changed.jstree", (e, data) => {
            this.treeChanged(data);
        });
        this.$tree.on("move_node.jstree", (e, data) => {
            var jstree = this.$tree.jstree(true);
            this.props.rendererActions.onDMSMoveNode(
                data.node,
                jstree.get_node(data.parent)
            );
        });
        this.$tree.on("rename_node.jstree", (e, data) => {
            this.props.rendererActions.onDMSRenameNode(data.node, data.text);
            this.updatePreview(data.node);
        });
        this.$tree.on("delete_node.jstree", (e, data) => {
            this.props.rendererActions.onDMSDeleteNode(data.node);
        });
        this.$tree.on("loaded.jstree", () => {
            this.$tree.jstree("open_all");
        });
    }

    treeChanged(data) {
        if (
            data.action === "select_node" &&
            data.selected &&
            data.selected.length === 1
        ) {
            this.updatePreview(data.node);
        }
    }

    updatePreview(node) {
        var $buttons = $(this.extra_actions.el);
        $buttons.empty();
        if (
            node.data &&
            ["dms.directory", "dms.file"].indexOf(node.data.resModel) !== -1
        ) {
            this.nodeSelectedState.data = {};
            this.nodeSelectedState.data = node.data;
            var menu = this.loadContextMenu(node);
            _.each(menu, (action) => {
                this.generateActionButton(node, action, $buttons);
            });
        }
    }

    loadContextMenu(node) {
        var menu = {};
        var jstree = this.$tree.jstree(true);
        if (node.data) {
            if (node.data.resModel === "dms.directory") {
                menu = this.loadContextMenuDirectoryBefore(jstree, node, menu);
                menu = this.loadContextMenuBasic(jstree, node, menu);
                menu = this.loadContextMenuDirectory(jstree, node, menu);
            } else if (node.data.resModel === "dms.file") {
                menu = this.loadContextMenuBasic(jstree, node, menu);
                menu = this.loadContextMenuFile(jstree, node, menu);
            }
        }
        return menu;
    }

    loadContextMenuBasic($jstree, node, menu) {
        menu.rename = {
            separator_before: false,
            separator_after: false,
            icon: "fa fa-pencil",
            label: _lt("Rename"),
            action: () => {
                $jstree.edit(node);
            },
            _disabled: () => {
                return !node.data.data.perm_write || node.data.data.storage;
            },
        };
        menu.action = {
            separator_before: false,
            separator_after: false,
            icon: "fa fa-bolt",
            label: _lt("Actions"),
            action: false,
            submenu: {
                cut: {
                    separator_before: false,
                    separator_after: false,
                    icon: "fa fa-scissors",
                    label: _lt("Cut"),
                    action: () => {
                        $jstree.cut(node);
                    },
                    _disabled: () => {
                        return !node.data.data.perm_read || node.data.data.storage;
                    },
                },
            },
            _disabled: () => {
                return !node.data.data.perm_read;
            },
        };
        menu.delete = {
            separator_before: false,
            separator_after: false,
            icon: "fa fa-trash-o",
            label: _lt("Delete"),
            action: () => {
                $jstree.delete_node(node);
            },
            _disabled: () => {
                return !node.data.data.perm_unlink || node.data.data.storage;
            },
        };
        menu.open = {
            separator_before: false,
            separator_after: false,
            icon: "fa fa-external-link",
            label: _lt("Open"),
            action: () => {
                this.onDMSOpenRecord(node);
            },
        };
        return menu;
    }

    loadContextMenuDirectoryBefore($jstree, node, menu) {
        menu.add_directory = {
            separator_before: false,
            separator_after: false,
            icon: "fa fa-folder",
            label: _lt("Create directory"),
            action: () => {
                this.onDMSAddDirectory(node);
            },
            _disabled: () => {
                return !node.data.data.perm_create;
            },
        };
        menu.add_file = {
            separator_before: false,
            separator_after: true,
            icon: "fa fa-file",
            label: _lt("Create File"),
            action: () => {
                this.onDMSAddFile(node);
            },
            _disabled: () => {
                return !node.data.data.perm_create;
            },
        };
        return menu;
    }

    loadContextMenuDirectory($jstree, node, menu) {
        if (menu.action && menu.action.submenu) {
            menu.action.submenu.paste = {
                separator_before: false,
                separator_after: false,
                icon: "fa fa-clipboard",
                label: _lt("Paste"),
                action: () => {
                    $jstree.paste(node);
                },
                _disabled: () => {
                    return !$jstree.can_paste() && !node.data.data.perm_create;
                },
            };
        }
        return menu;
    }

    loadContextMenuFile($jstree, node, menu) {
        menu.preview = {
            separator_before: false,
            separator_after: false,
            icon: "fa fa-eye",
            label: _lt("Preview"),
            action: () => {
                this.onDMSPreviewFile(node);
            },
        };
        menu.download = {
            separator_before: false,
            separator_after: false,
            icon: "fa fa-download",
            label: _lt("Download"),
            action: () => {
                download({
                    url: "/web/content",
                    data: {
                        id: node.data.data.id,
                        download: true,
                        field: "content",
                        model: "dms.file",
                        filename_field: "name",
                        filename: node.data.data.filename,
                    },
                });
            },
        };
        return menu;
    }

    generateActionButton(node, action, $buttons) {
        if (action.action) {
            var $button = $("<button>", {
                type: "button",
                class: "btn btn-secondary " + action.icon,
                "data-toggle": "dropdown",
                title: action.label,
            }).on("click", (event) => {
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
            _.each(action.submenu, (sub_action) => {
                this.generateActionButton(node, sub_action, $buttons);
            });
        }
    }

    async loadData(node, callback) {
        const {result, empty_storages} = await this.props.rendererActions.onDMSLoad(
            node
        );
        result.then((data) => {
            callback.call(this, data);
            if (empty_storages.length > 0) {
                $(this.dms_add_directory.el).removeClass("o_hidden");
            }
        });
    }

    /*
        This is used to check that the operation is allowed
    */
    checkCallback(operation, node, parent) {
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
            if (parent.data && parent.data.resModel === "dms.storage") {
                return false;
            }
            // Prevent moving a child to a file
            if (parent.data && parent.data.resModel === "dms.file") {
                return false;
            }
        }
        return true;
    }
    checkSelect(node) {
        if (this.props.filesOnly && node.data.resModel !== "dms.file") {
            return false;
        }
        return !(node.parent === "#" && node.data.resModel === "dms.storage");
    }
    onDMSAddDirectory(node) {
        var context = {
            default_parent_directory_id: node.data.data.id,
        };
        this.dialog.add(FormViewDialog, {
            resModel: "dms.directory",
            context: context,
            title: _lt("Add Directory: ") + node.data.data.name,
            onRecordSaved: () => {
                const selected_id = this.$tree.find(".jstree-clicked").attr("id");
                const model_data = this.$tree.jstree(true)._model.data;
                const state = this.$tree.jstree(true).get_state();
                const open_res_ids = state.core.open.map(
                    (id) => model_data[id].data.data.id
                );
                this.$tree.on("refresh_node.jstree", () => {
                    const model_data_entries = Object.entries(model_data);
                    const ids = model_data_entries
                        .filter(
                            ([, value]) =>
                                value.data &&
                                open_res_ids.includes(value.data.data.id) &&
                                value.data.resModel === "dms.directory"
                        )
                        .map((tuple) => tuple[0]);
                    for (var id of ids) {
                        this.$tree.jstree(true).open_node(id);
                    }
                });
                this.$tree.jstree(true).refresh_node(selected_id);
            },
        });
    }
    onDMSAddFile(node) {
        var context = {
            default_directory_id: node.data.data.id,
        };
        this.dialog.add(FormViewDialog, {
            resModel: "dms.file",
            context: context,
            title: _lt("Add File: ") + node.data.data.name,
            onRecordSaved: () => {
                const selected_id = this.$tree.find(".jstree-clicked").attr("id");
                const model_data = this.$tree.jstree(true)._model.data;
                const state = this.$tree.jstree(true).get_state();
                const open_res_ids = state.core.open.map(
                    (id) => model_data[id].data.data.id
                );
                this.$tree.on("refresh_node.jstree", () => {
                    const model_data_entries = Object.entries(model_data);
                    const ids = model_data_entries
                        .filter(
                            ([, value]) =>
                                value.data &&
                                open_res_ids.includes(value.data.data.id) &&
                                value.data.model === "dms.directory"
                        )
                        .map((tuple) => tuple[0]);
                    for (var id of ids) {
                        this.$tree.jstree(true).open_node(id);
                    }
                });
                this.$tree.jstree(true).refresh_node(selected_id);
            },
        });
    }
    onDMSAddDirectoryRecord() {
        this.props.rendererActions.onDMSCreateEmptyStorages().then(() => {
            this.$tree.jstree(true).refresh();
            $(this.dms_add_directory.el).addClass("o_hidden");
        });
    }
    onDMSOpenRecord(node) {
        this.dialog.add(FormViewDialog, {
            resModel: node.data.resModel,
            title: _lt("Open: ") + node.data.data.name,
            resId: node.data.data.id,
        });
    }
    onDMSPreviewFile(node) {
        this.messaging.get().then((messaging) => {
            const attachmentList = messaging.models.AttachmentList.insert({
                selectedAttachment: messaging.models.Attachment.insert({
                    id: node.data.data.id,
                    filename: node.data.data.name,
                    name: node.data.data.name,
                    mimetype: node.data.data.mimetype,
                    model_name: node.data.resModel,
                }),
            });
            Component.env.services.dialog = messaging.models.Dialog.insert({
                attachmentListOwnerAsAttachmentView: attachmentList,
            });
        });
    }
    get showDragZone() {
        return (
            this.nodeSelectedState.data.resModel === "dms.directory" &&
            this.dragState.showDragZone
        );
    }
    highlight(ev) {
        ev.stopPropagation();
        ev.preventDefault();
        this.dragState.showDragZone = true;
    }
    unhighlight(ev) {
        ev.stopPropagation();
        ev.preventDefault();
        this.dragState.showDragZone = false;
    }
    async onDrop(ev) {
        ev.preventDefault();
        const directoryId = this.nodeSelectedState.data.data.id;
        const res = await this.props.rendererActions
            .onDMSDroppedFile(directoryId, ev.dataTransfer.files)
            .catch((error) => {
                this.notification.add(error.data.message, {
                    type: "danger",
                });
            });
        if (res === "no_attachments") {
            this.notification.add(_lt("An error occurred during the upload"));
        } else {
            const selected_id = this.$tree.find(".jstree-clicked").attr("id");
            const model_data = this.$tree.jstree(true)._model.data;
            const state = this.$tree.jstree(true).get_state();
            const open_res_ids = state.core.open.map(
                (id) => model_data[id].data.data.id
            );
            this.$tree.on("refresh_node.jstree", () => {
                const model_data_entries = Object.entries(model_data);
                const ids = model_data_entries
                    .filter(
                        ([, value]) =>
                            value.data &&
                            open_res_ids.includes(value.data.data.id) &&
                            value.data.model === "dms.directory"
                    )
                    .map((tuple) => tuple[0]);
                for (var id of ids) {
                    this.$tree.jstree(true).open_node(id);
                }
            });
            this.$tree.jstree(true).refresh_node(selected_id);
        }
        this.unhighlight(ev);
    }
}

DmsListRenderer.template = "dms_list.Renderer";
