/* Copyright 2024 Tecnativa - Carlos Roca
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl). */
import {Component, proxy, signal, t, useOnChange, useProps} from "@odoo/owl";
import {ConfirmationDialog} from "@web/core/confirmation_dialog/confirmation_dialog";
import {DmsContextMenu} from "../../components/dms_context_menu/dms_context_menu.esm";
import {DmsTree} from "../../components/dms_tree/dms_tree.esm";
import {DmsTreeModel} from "../../components/dms_tree/dms_tree_model.esm";
import {FormViewDialog} from "@web/views/view_dialogs/form_view_dialog";
import {_t} from "@web/core/l10n/translation";
import {download} from "@web/core/network/download";
import {useDropzone} from "@web/core/dropzone/dropzone_hook";
import {useFileViewer} from "@web/core/file_viewer/file_viewer_hook";
import {usePopover} from "@web/core/popover/popover_hook";
import {useService} from "@web/core/utils/hooks";

export class DmsListRenderer extends Component {
    static template = "dms_list.Renderer";
    static components = {DmsTree};

    props = useProps({
        rendererActions: t.object(),
        record: t.object().optional(),
        readonly: t.boolean().optional(),
        // Only allow selecting files
        filesOnly: t.boolean().optional(false),
    });

    dropZone = signal.ref();

    setup() {
        this.store = useService("mail.store");
        this.fileViewer = useFileViewer();
        this.notification = useService("notification");
        this.dialog = useService("dialog");
        this.ui = useService("ui");
        this.state = proxy({
            // Data of the selected node: {resModel, data}
            selected: {},
            hasEmptyStorages: false,
        });
        this.tree = proxy(
            new DmsTreeModel({
                loadNodes: (node) => this.loadNodes(node),
                canSelect: (node) => this.checkSelect(node),
                onSelect: (node) => this.updatePreview(node),
                onRename: (node, text) =>
                    this.props.rendererActions.onDMSRenameNode(node, text),
                onMove: (node, parent) =>
                    this.props.rendererActions.onDMSMoveNode(node, parent),
                // Same rules as the "Cut" and "Paste" actions
                canDrag: (node) => this.canMoveNode(node),
                canDrop: (node, parent) => Boolean(parent.data.data?.perm_create),
            })
        );
        this.contextMenu = usePopover(DmsContextMenu, {
            position: "bottom-start",
            popoverClass: "o-dropdown--menu dropdown-menu mx-0 py-0",
            animation: false,
            arrow: false,
        });

        // Upload the files dropped on the details of the selected folder
        useDropzone(
            this.dropZone,
            (ev) => this.onDrop(ev),
            "o_dms_dropzone",
            () => this.state.selected.resModel === "dms.directory"
        );

        // Load the tree again when the related record changes (e.g. when
        // navigating between records of a form view).
        useOnChange(
            () => [this.props.record?.resId],
            () => this.tree.load()
        );
    }

    // -------------------------------------------------------------------------
    // Data
    // -------------------------------------------------------------------------

    /**
     * @param {import("../../components/dms_tree/dms_tree_model.esm").DmsTreeNode|null} node
     * @returns {Promise<Object[]>}
     */
    async loadNodes(node) {
        const {result, empty_storages} =
            await this.props.rendererActions.onDMSLoad(node);
        if (!node) {
            this.state.hasEmptyStorages = empty_storages.length > 0;
        }
        return result;
    }

    // -------------------------------------------------------------------------
    // Selection / preview
    // -------------------------------------------------------------------------

    /**
     * @param {import("../../components/dms_tree/dms_tree_model.esm").DmsTreeNode} node
     * @returns {Boolean}
     */
    checkSelect(node) {
        if (this.props.filesOnly && node.data.resModel !== "dms.file") {
            return false;
        }
        return !(!node.parentId && node.data.resModel === "dms.storage");
    }

    /**
     * @param {import("../../components/dms_tree/dms_tree_model.esm").DmsTreeNode} node
     * @returns {Boolean} whether the node can be cut or dragged
     */
    canMoveNode(node) {
        const values = node.data?.data;
        return (
            ["dms.directory", "dms.file"].includes(node.data?.resModel) &&
            Boolean(values?.perm_read) &&
            !values.storage
        );
    }

    updatePreview(node) {
        if (node?.data && ["dms.directory", "dms.file"].includes(node.data.resModel)) {
            this.state.selected = node.data;
        } else {
            this.state.selected = {};
        }
    }

    get selectedNode() {
        return this.tree.selectedNode;
    }

    /**
     * @returns {Array} actions of the selected node, shown as buttons
     */
    get selectedActions() {
        const node = this.selectedNode;
        if (!node || !this.state.selected.resModel) {
            return [];
        }
        return this.getNodeActions(node);
    }

    // -------------------------------------------------------------------------
    // Actions
    // -------------------------------------------------------------------------

    /**
     * The actions available for a node, in the order they are shown. Each
     * action is {key, label, icon, separatorBefore, disabled, run}.
     *
     * @param {import("../../components/dms_tree/dms_tree_model.esm").DmsTreeNode} node
     * @returns {Array}
     */
    getNodeActions(node) {
        const menu = this.loadContextMenu(node);
        return Object.entries(menu).map(([key, action]) => ({
            key,
            label: action.label,
            icon: action.icon,
            separatorBefore: Boolean(action.separator_before),
            disabled: Boolean(action._disabled && action._disabled()),
            run: action.action,
        }));
    }

    /**
     * Kept with the same structure as the former jsTree context menu, so that
     * other modules can add or alter entries.
     *
     * @param {Object} node
     * @returns {Object} {key: {label, icon, action, _disabled, separator_before}}
     */
    loadContextMenu(node) {
        let menu = {};
        if (node?.data?.resModel === "dms.directory") {
            menu = this.loadContextMenuDirectoryBefore(node, menu);
            menu = this.loadContextMenuBasic(node, menu);
            menu = this.loadContextMenuDirectory(node, menu);
        } else if (node?.data?.resModel === "dms.file") {
            menu = this.loadContextMenuBasic(node, menu);
            menu = this.loadContextMenuFile(node, menu);
        }
        return menu;
    }

    loadContextMenuDirectoryBefore(node, menu) {
        menu.add_directory = {
            icon: "folder",
            label: _t("Create directory"),
            action: () => this.onDMSAddDirectory(node),
            _disabled: () => !node.data.data.perm_create,
        };
        menu.add_file = {
            icon: "description",
            label: _t("Create File"),
            action: () => this.onDMSAddFile(node),
            _disabled: () => !node.data.data.perm_create,
        };
        return menu;
    }

    loadContextMenuBasic(node, menu) {
        menu.rename = {
            icon: "edit",
            label: _t("Rename"),
            separator_before: true,
            action: () => this.tree.startRename(node),
            _disabled: () => !node.data.data.perm_write || node.data.data.storage,
        };
        menu.cut = {
            icon: "content_cut",
            label: _t("Cut"),
            action: () => this.tree.cut(node),
            _disabled: () => !this.canMoveNode(node),
        };
        menu.delete = {
            icon: "delete",
            label: _t("Delete"),
            action: () => this.onDMSDeleteNode(node),
            _disabled: () => !node.data.data.perm_unlink || node.data.data.storage,
        };
        menu.open = {
            icon: "open_in_new",
            label: _t("Open"),
            action: () => this.onDMSOpenRecord(node),
        };
        return menu;
    }

    loadContextMenuDirectory(node, menu) {
        const entries = Object.entries(menu);
        const cutIndex = entries.findIndex(([key]) => key === "cut");
        // Show "Paste" right after "Cut"
        entries.splice(cutIndex + 1, 0, [
            "paste",
            {
                icon: "content_paste",
                label: _t("Paste"),
                action: () => this.tree.paste(node),
                _disabled: () =>
                    !node.data.data.perm_create || !this.tree.canPaste(node),
            },
        ]);
        return Object.fromEntries(entries);
    }

    loadContextMenuFile(node, menu) {
        menu.preview = {
            icon: "visibility",
            label: _t("Preview"),
            separator_before: true,
            action: () => this.onDMSPreviewFile(node),
        };
        menu.download = {
            icon: "download",
            label: _t("Download"),
            action: () => this.onDMSDownloadFile(node),
        };
        return menu;
    }

    /**
     * Run an action of the node if it is available. Used by the keyboard
     * shortcuts of the tree.
     *
     * @param {String} key
     * @param {Object} node
     * @returns {Boolean} whether the action has been run
     */
    runNodeAction(key, node) {
        const action = this.getNodeActions(node).find((a) => a.key === key);
        if (!action || action.disabled) {
            return false;
        }
        action.run();
        return true;
    }

    /**
     * @param {Object} node
     * @param {HTMLElement} target
     */
    openContextMenu(node, target) {
        const actions = this.getNodeActions(node);
        if (!actions.length || !target) {
            return;
        }
        this.contextMenu.open(target, {actions});
    }

    onClickAction(action) {
        if (!action.disabled) {
            action.run();
        }
    }

    // -------------------------------------------------------------------------
    // Handlers
    // -------------------------------------------------------------------------

    onDMSAddDirectory(node) {
        this.dialog.add(FormViewDialog, {
            resModel: "dms.directory",
            context: {
                default_parent_directory_id: node.data.data.id,
            },
            title: _t("Add Directory: %s", node.data.data.name),
            onRecordSaved: () => this.tree.reload(node),
        });
    }

    onDMSAddFile(node) {
        this.dialog.add(FormViewDialog, {
            resModel: "dms.file",
            context: {
                default_directory_id: node.data.data.id,
            },
            title: _t("Add File: %s", node.data.data.name),
            onRecordSaved: () => this.tree.reload(node),
        });
    }

    onDMSDeleteNode(node) {
        this.dialog.add(ConfirmationDialog, {
            title: _t("Delete"),
            body: _t("Are you sure you want to delete “%s”?", node.text),
            confirmLabel: _t("Delete"),
            confirm: async () => {
                await this.props.rendererActions.onDMSDeleteNode(node);
                this.tree.remove(node);
            },
            cancel: () => undefined,
        });
    }

    async onDMSAddDirectoryRecord() {
        await this.props.rendererActions.onDMSCreateEmptyStorages();
        await this.tree.load({keepState: true});
    }

    onDMSOpenRecord(node) {
        this.dialog.add(FormViewDialog, {
            resModel: node.data.resModel,
            title: _t("Open: %s", node.data.data.name),
            resId: node.data.data.id,
            onRecordSaved: () => {
                const parent = this.tree.getParent(node);
                return parent
                    ? this.tree.reload(parent)
                    : this.tree.load({keepState: true});
            },
        });
    }

    onDMSPreviewFile(node) {
        const attachment = this.store["ir.attachment"].insert({
            id: node.data.data.id,
            filename: node.data.data.name,
            name: node.data.data.name,
            mimetype: node.data.data.mimetype,
            model_name: node.data.resModel,
        });
        this.fileViewer.open(attachment);
    }

    onDMSDownloadFile(node) {
        return download({
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
    }

    // -------------------------------------------------------------------------
    // Drag and drop of files to upload
    // -------------------------------------------------------------------------

    async onDrop(ev) {
        ev.preventDefault();
        const node = this.selectedNode;
        if (node?.data.resModel !== "dms.directory") {
            return;
        }
        const files = ev.dataTransfer?.files;
        if (!files?.length) {
            return;
        }
        const {ids, errors} = await this.props.rendererActions.onDMSDroppedFile(
            node.data.data.id,
            files
        );
        for (const error of errors) {
            this.notification.add(error, {type: "danger", sticky: true});
        }
        if (!ids.length && !errors.length) {
            this.notification.add(_t("An error occurred during the upload"), {
                type: "danger",
            });
        }
        if (ids.length) {
            await this.tree.reload(node);
        }
    }
}
