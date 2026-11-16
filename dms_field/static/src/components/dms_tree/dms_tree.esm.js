/* Copyright 2026 Tecnativa - Carlos Roca
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl). */
import {Component, onWillDestroy, signal, t, useOnChange, useProps} from "@odoo/owl";
import {_t} from "@web/core/l10n/translation";
import {mimetype2icon} from "../../utils/mimetype.esm";

// Data type of the nodes dragged inside the tree. It is not "Files", so the
// upload dropzones ignore these drags.
export const DMS_NODE_MIMETYPE = "application/x-dms-tree-node";
// Time hovering a closed folder while dragging before it is opened (ms)
const DRAG_EXPAND_DELAY = 700;

/**
 * @param {import("./dms_tree_model.esm").DmsTreeNode} node
 * @returns {String} Material Symbols icon name
 */
export function getNodeIcon(node) {
    switch (node.data?.resModel) {
        case "dms.storage":
            return "database";
        case "dms.directory":
            return node.isOpen ? "folder_open" : "folder";
        case "dms.file":
            return mimetype2icon(node.data.data?.mimetype);
    }
    return "description";
}

export class DmsTreeNode extends Component {
    static template = "dms_field.DmsTreeNode";

    props = useProps({
        node: t.object(),
        tree: t.object(),
    });

    rootRef = signal.ref();
    inputRef = signal.ref();

    setup() {
        // Move the DOM focus along with the keyboard navigation
        useOnChange(
            () => [this.isFocused, this.rootRef()],
            (isFocused, el) => {
                if (isFocused && el && this.props.tree.hasFocusWithin()) {
                    el.focus();
                }
            }
        );
        useOnChange(
            () => [this.inputRef()],
            (input) => {
                if (input) {
                    input.focus();
                    input.select();
                }
            }
        );
    }

    get model() {
        return this.props.tree.props.model;
    }

    get node() {
        return this.props.node;
    }

    get level() {
        return this.model.getLevel(this.node);
    }

    get icon() {
        return getNodeIcon(this.node);
    }

    get isSelected() {
        return this.model.selectedId === this.node.id;
    }

    get isFocused() {
        const focused = this.model.focusedNode || this.model.roots[0];
        return focused?.id === this.node.id;
    }

    get isRenaming() {
        return this.model.renamingId === this.node.id;
    }

    get editableName() {
        return this.model.getEditableName(this.node);
    }

    get isCut() {
        return this.model.cutId === this.node.id;
    }

    get isDraggable() {
        return this.model.canDrag(this.node);
    }

    get isDragging() {
        return this.model.dragId === this.node.id;
    }

    get isDropTarget() {
        return this.model.dropTargetId === this.node.id;
    }

    get toggleTitle() {
        return this.node.isOpen ? _t("Collapse") : _t("Expand");
    }

    onFocus(ev) {
        // Keep the model in sync when the node gets the focus without a click
        // (e.g. with the Tab key)
        if (
            ev.target === this.rootRef() &&
            this.model.focusedNode?.id !== this.node.id
        ) {
            this.model.focus(this.node);
        }
    }

    onClickRow() {
        this.model.select(this.node);
    }

    onDblClickRow() {
        this.model.toggle(this.node);
    }

    onDblClickLabel() {
        // Rename the node, or open/close it if it can't be renamed
        if (!this.props.tree.props.onAction("rename", this.node)) {
            this.model.toggle(this.node);
        }
    }

    onClickToggle() {
        this.model.focus(this.node);
        this.model.toggle(this.node);
    }

    onContextMenu(ev) {
        ev.preventDefault();
        ev.stopPropagation();
        this.props.tree.openContextMenu(this.node, ev.currentTarget);
    }

    onRenameKeydown(ev) {
        // Keep the keys for the input, not for the tree navigation
        ev.stopPropagation();
        if (ev.key === "Enter") {
            ev.preventDefault();
            this.commitRename(ev.target.value);
        } else if (ev.key === "Escape") {
            ev.preventDefault();
            this.model.cancelRename();
            this.rootRef()?.focus();
        }
    }

    onRenameBlur(ev) {
        if (this.isRenaming) {
            this.commitRename(ev.target.value);
        }
    }

    commitRename(value) {
        return this.model.rename(this.node, value);
    }

    // -------------------------------------------------------------------------
    // Drag and drop to move nodes
    // -------------------------------------------------------------------------

    /**
     * @param {DragEvent} ev
     */
    onDragStart(ev) {
        // Only the row of this node, not the ones of its children
        ev.stopPropagation();
        if (!this.model.startDrag(this.node)) {
            ev.preventDefault();
            return;
        }
        ev.dataTransfer.setData(DMS_NODE_MIMETYPE, this.node.id);
        ev.dataTransfer.effectAllowed = "move";
    }

    /**
     * @param {DragEvent} ev
     */
    onDragOver(ev) {
        if (!this.model.dragId) {
            // Not a node of this tree (e.g. files from the computer)
            return;
        }
        const target = this.model.dragOver(this.node);
        if (!target) {
            ev.dataTransfer.dropEffect = "none";
            this.props.tree.cancelExpand();
            return;
        }
        ev.preventDefault();
        ev.dataTransfer.dropEffect = "move";
        this.props.tree.scheduleExpand(target === this.node ? this.node : null);
    }

    /**
     * @param {DragEvent} ev
     */
    onDrop(ev) {
        if (!this.model.dragId) {
            return;
        }
        ev.preventDefault();
        ev.stopPropagation();
        this.props.tree.cancelExpand();
        return this.model.drop(this.node);
    }

    onDragEnd() {
        this.props.tree.cancelExpand();
        this.model.endDrag();
    }
}
DmsTreeNode.components = {DmsTreeNode};

export class DmsTree extends Component {
    static template = "dms_field.DmsTree";
    static components = {DmsTreeNode};

    props = useProps({
        model: t.object(),
        // (node, targetElement) => void
        onContextMenu: t.function().optional(() => () => undefined),
        // (actionKey, node) => Boolean (whether the action has been run), used
        // for the keyboard shortcuts (F2, Delete) and the double click on names
        onAction: t.function().optional(() => () => false),
    });

    rootRef = signal.ref();

    setup() {
        this.expandTimeout = null;
        this.expandNodeId = null;
        onWillDestroy(() => this.cancelExpand());
    }

    get model() {
        return this.props.model;
    }

    /**
     * Open the closed folder hovered while dragging after a short delay.
     *
     * @param {import("./dms_tree_model.esm").DmsTreeNode|null} node
     */
    scheduleExpand(node) {
        if (!node || node.isOpen || !node.hasChildren) {
            this.cancelExpand();
            return;
        }
        if (this.expandNodeId === node.id) {
            return;
        }
        this.cancelExpand();
        this.expandNodeId = node.id;
        this.expandTimeout = setTimeout(() => {
            this.expandTimeout = null;
            this.expandNodeId = null;
            if (this.model.dragId) {
                this.model.open(node);
            }
        }, DRAG_EXPAND_DELAY);
    }

    cancelExpand() {
        clearTimeout(this.expandTimeout);
        this.expandTimeout = null;
        this.expandNodeId = null;
    }

    /**
     * @param {DragEvent} ev
     */
    onDragLeave(ev) {
        if (this.model.dragId && !this.rootRef()?.contains(ev.relatedTarget)) {
            this.cancelExpand();
            this.model.dragOver(null);
        }
    }

    hasFocusWithin() {
        const el = this.rootRef();
        return Boolean(el && el.contains(document.activeElement));
    }

    openContextMenu(node, target) {
        this.model.select(node);
        this.props.onContextMenu(node, target);
    }

    /**
     * Keyboard navigation, following the WAI-ARIA tree view pattern.
     *
     * @param {KeyboardEvent} ev
     */
    onKeydown(ev) {
        if (ev.target.closest("input, textarea")) {
            return;
        }
        const visibleNodes = this.model.getVisibleNodes();
        if (!visibleNodes.length) {
            return;
        }
        const key = ev.shiftKey && ev.key === "F10" ? "ContextMenu" : ev.key;
        const handler = this.keyHandlers[key];
        if (!handler) {
            return;
        }
        const node = this.model.focusedNode || visibleNodes[0];
        handler(node, visibleNodes);
        ev.preventDefault();
        ev.stopPropagation();
    }

    /**
     * @returns {Object} {key: (node, visibleNodes) => void}
     */
    get keyHandlers() {
        const focusAt = (visibleNodes, index) =>
            this.model.focus(
                visibleNodes[Math.max(0, Math.min(index, visibleNodes.length - 1))]
            );
        const indexOf = (visibleNodes, node) =>
            visibleNodes.findIndex((n) => n.id === node.id);
        const openContextMenu = (node) =>
            this.openContextMenu(node, this.getRowElement(node));
        const select = (node) => this.model.select(node);
        return {
            ArrowDown: (node, nodes) => focusAt(nodes, indexOf(nodes, node) + 1),
            ArrowUp: (node, nodes) => focusAt(nodes, indexOf(nodes, node) - 1),
            Home: (node, nodes) => focusAt(nodes, 0),
            End: (node, nodes) => focusAt(nodes, nodes.length - 1),
            ArrowRight: (node) => this.expandOrFocusChild(node),
            ArrowLeft: (node) => this.collapseOrFocusParent(node),
            Enter: select,
            " ": select,
            F2: (node) => this.props.onAction("rename", node),
            Delete: (node) => this.props.onAction("delete", node),
            ContextMenu: openContextMenu,
        };
    }

    expandOrFocusChild(node) {
        if (node.hasChildren && !node.isOpen) {
            this.model.open(node);
        } else if (node.isOpen && node.children.length) {
            this.model.focus(node.children[0]);
        }
    }

    collapseOrFocusParent(node) {
        if (node.isOpen) {
            this.model.close(node);
            return;
        }
        const parent = this.model.getParent(node);
        if (parent) {
            this.model.focus(parent);
        }
    }

    /**
     * @param {import("./dms_tree_model.esm").DmsTreeNode} node
     * @returns {HTMLElement|null}
     */
    getRowElement(node) {
        return (
            this.rootRef()?.querySelector(
                `[data-node-id="${CSS.escape(node.id)}"] > .o_dms_tree_row`
            ) || null
        );
    }
}
