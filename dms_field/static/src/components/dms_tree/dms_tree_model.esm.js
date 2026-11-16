/* Copyright 2026 Tecnativa - Carlos Roca
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl). */
import {markRaw} from "@odoo/owl";

/**
 * @typedef DmsTreeNode
 * @property {String} id unique and stable id (e.g. "dms.directory_5")
 * @property {String} text label shown in the tree
 * @property {String} type "storage", "directory" or "file"
 * @property {{resModel: String, data: Object}} data record values
 * @property {String|null} parentId
 * @property {DmsTreeNode[]} children
 * @property {Boolean} hasChildren whether the node has (or may have) children
 * @property {Boolean} isLoaded whether the children have been fetched
 * @property {Boolean} isOpen
 * @property {Boolean} isLoading
 *
 * @typedef DmsTreeModelParams
 * @property {(node: DmsTreeNode|null) => Promise<Object[]>} loadNodes returns
 *  the raw children of the given node (the root nodes if node is null). A raw
 *  node is {id, text, type, data, children} where children is either an array
 *  of raw nodes or a boolean telling whether there are children to load.
 * @property {(node: DmsTreeNode) => Boolean} [canSelect]
 * @property {(node: DmsTreeNode|null) => void} [onSelect]
 * @property {(node: DmsTreeNode, text: String) => Promise} [onRename]
 * @property {(node: DmsTreeNode, parent: DmsTreeNode) => Promise} [onMove]
 * @property {(node: DmsTreeNode) => Boolean} [canDrag] whether the node can be
 *  dragged to move it
 * @property {(node: DmsTreeNode, parent: DmsTreeNode) => Boolean} [canDrop]
 *  extra rules (e.g. access rights) to move the node into the parent
 */

/**
 * Folders first, then files, each group sorted by name.
 *
 * @param {DmsTreeNode} a
 * @param {DmsTreeNode} b
 * @returns {Number}
 */
export function compareNodes(a, b) {
    const modelA = a.data?.resModel || "";
    const modelB = b.data?.resModel || "";
    if (modelA !== modelB) {
        return modelA > modelB ? 1 : -1;
    }
    return (a.text || "").localeCompare(b.text || "", undefined, {
        numeric: true,
        sensitivity: "base",
    });
}

/**
 * Split a file name in its base name and its extension, like os.path.splitext
 * does: "report.final.pdf" => ["report.final", ".pdf"], ".bashrc" =>
 * [".bashrc", ""].
 *
 * @param {String} name
 * @returns {{base: String, extension: String}}
 */
export function splitFileName(name) {
    const index = name.lastIndexOf(".");
    // Leading dots don't start an extension
    if (index <= 0 || /^\.+$/.test(name.slice(0, index + 1))) {
        return {base: name, extension: ""};
    }
    return {base: name.slice(0, index), extension: name.slice(index)};
}

/**
 * Reactive state and operations of the DMS tree. It is UI agnostic: the
 * components only render it and call its methods. It must be wrapped with
 * `proxy()` so that the components are rendered on changes.
 */
export class DmsTreeModel {
    /**
     * @param {DmsTreeModelParams} params
     */
    constructor(params) {
        this.params = markRaw({
            canSelect: () => true,
            onSelect: () => undefined,
            onRename: () => Promise.resolve(),
            onMove: () => Promise.resolve(),
            canDrag: () => true,
            canDrop: () => true,
            ...params,
        });
        /** @type {DmsTreeNode[]} */
        this.roots = [];
        this.isLoading = false;
        this.selectedId = null;
        this.focusedId = null;
        this.renamingId = null;
        this.cutId = null;
        // Node being dragged and folder that would receive it
        this.dragId = null;
        this.dropTargetId = null;
        this.loadId = 0;
    }

    // -------------------------------------------------------------------------
    // Getters
    // -------------------------------------------------------------------------

    get selectedNode() {
        return this.findNode(this.selectedId);
    }

    get focusedNode() {
        return this.findNode(this.focusedId) || this.selectedNode;
    }

    get cutNode() {
        return this.findNode(this.cutId);
    }

    get dragNode() {
        return this.findNode(this.dragId);
    }

    /**
     * @param {String|null} id
     * @param {DmsTreeNode[]} [nodes]
     * @returns {DmsTreeNode|null}
     */
    findNode(id, nodes = this.roots) {
        if (!id) {
            return null;
        }
        for (const node of nodes) {
            if (node.id === id) {
                return node;
            }
            const found = this.findNode(id, node.children);
            if (found) {
                return found;
            }
        }
        return null;
    }

    /**
     * @param {DmsTreeNode} node
     * @returns {DmsTreeNode|null}
     */
    getParent(node) {
        return this.findNode(node.parentId);
    }

    /**
     * @param {DmsTreeNode} node
     * @returns {DmsTreeNode[]} the list containing the node
     */
    getSiblings(node) {
        const parent = this.getParent(node);
        return parent ? parent.children : this.roots;
    }

    /**
     * @param {DmsTreeNode} node
     * @param {DmsTreeNode} ancestor
     * @returns {Boolean}
     */
    isDescendant(node, ancestor) {
        let parent = this.getParent(node);
        while (parent) {
            if (parent.id === ancestor.id) {
                return true;
            }
            parent = this.getParent(parent);
        }
        return false;
    }

    /**
     * @param {DmsTreeNode} node
     * @returns {Number} 1 for the root nodes
     */
    getLevel(node) {
        let level = 1;
        let parent = this.getParent(node);
        while (parent) {
            level++;
            parent = this.getParent(parent);
        }
        return level;
    }

    /**
     * @returns {DmsTreeNode[]} the nodes shown on screen, in display order
     */
    getVisibleNodes(nodes = this.roots, result = []) {
        for (const node of nodes) {
            result.push(node);
            if (node.isOpen) {
                this.getVisibleNodes(node.children, result);
            }
        }
        return result;
    }

    /**
     * @param {DmsTreeNode[]} nodes
     * @param {DmsTreeNode[]} [result]
     * @returns {DmsTreeNode[]} the given nodes and all their loaded descendants
     */
    getAllNodes(nodes = this.roots, result = []) {
        for (const node of nodes) {
            result.push(node);
            this.getAllNodes(node.children, result);
        }
        return result;
    }

    // -------------------------------------------------------------------------
    // Loading
    // -------------------------------------------------------------------------

    /**
     * Load the root nodes and open the whole tree.
     *
     * @param {Object} [options]
     * @param {Boolean} [options.keepState] reopen the nodes that were open and
     *  keep the selection instead of opening the whole tree.
     */
    async load({keepState = false} = {}) {
        const loadId = ++this.loadId;
        const openIds = keepState ? this._getOpenIds(this.roots) : null;
        const selectedId = keepState ? this.selectedId : null;
        this.isLoading = true;
        try {
            const rawNodes = await this.params.loadNodes(null);
            if (loadId !== this.loadId) {
                // A more recent load has been requested in the meantime
                return;
            }
            this.roots = this._makeNodes(rawNodes, null);
            this.renamingId = null;
            this.cutId = null;
            this.endDrag();
            if (keepState) {
                await this._restoreOpen(this.roots, openIds);
            } else {
                await this.expandAll();
            }
        } finally {
            if (loadId === this.loadId) {
                this.isLoading = false;
            }
        }
        if (loadId === this.loadId) {
            this._restoreSelection(selectedId);
        }
    }

    /**
     * Fetch again the children of the node, keeping open the ones that were.
     *
     * @param {DmsTreeNode} node
     */
    async reload(node) {
        const openIds = this._getOpenIds(node.children);
        await this._loadChildren(node);
        node.isOpen = node.hasChildren;
        await this._restoreOpen(node.children, openIds);
        this._restoreSelection(this.selectedId);
    }

    /**
     * @param {DmsTreeNode[]} [nodes]
     */
    async expandAll(nodes = this.roots) {
        await Promise.all(
            nodes.map(async (node) => {
                if (!node.hasChildren) {
                    return;
                }
                await this.open(node);
                await this.expandAll(node.children);
            })
        );
    }

    // -------------------------------------------------------------------------
    // Open / close
    // -------------------------------------------------------------------------

    /**
     * @param {DmsTreeNode} node
     */
    async open(node) {
        if (!node.hasChildren) {
            return;
        }
        if (!node.isLoaded) {
            await this._loadChildren(node);
        }
        node.isOpen = node.hasChildren;
    }

    /**
     * @param {DmsTreeNode} node
     */
    close(node) {
        node.isOpen = false;
        // The focus can't stay on a hidden node
        const focused = this.findNode(this.focusedId);
        if (focused && this.isDescendant(focused, node)) {
            this.focusedId = node.id;
        }
    }

    /**
     * @param {DmsTreeNode} node
     */
    async toggle(node) {
        if (node.isOpen) {
            this.close(node);
        } else {
            await this.open(node);
        }
    }

    // -------------------------------------------------------------------------
    // Selection / focus
    // -------------------------------------------------------------------------

    /**
     * @param {DmsTreeNode} node
     * @returns {Boolean}
     */
    canSelect(node) {
        return Boolean(node) && this.params.canSelect(node);
    }

    /**
     * @param {DmsTreeNode} node
     * @returns {Boolean} whether the node has been selected
     */
    select(node) {
        this.focusedId = node.id;
        if (!this.canSelect(node)) {
            return false;
        }
        this.selectedId = node.id;
        this.params.onSelect(node);
        return true;
    }

    unselect() {
        this.selectedId = null;
        this.params.onSelect(null);
    }

    /**
     * @param {DmsTreeNode} node
     */
    focus(node) {
        this.focusedId = node.id;
    }

    // -------------------------------------------------------------------------
    // Edition
    // -------------------------------------------------------------------------

    /**
     * @param {DmsTreeNode} node
     */
    startRename(node) {
        this.renamingId = node.id;
    }

    cancelRename() {
        this.renamingId = null;
    }

    /**
     * The part of the name that can be renamed: the extension of the files
     * is kept.
     *
     * @param {DmsTreeNode} node
     * @returns {{base: String, extension: String}}
     */
    getEditableName(node) {
        if (node.data?.resModel === "dms.file") {
            return splitFileName(node.text || "");
        }
        return {base: node.text || "", extension: ""};
    }

    /**
     * @param {DmsTreeNode} node
     * @param {String} text new name, without the extension for the files
     */
    async rename(node, text) {
        this.renamingId = null;
        const base = (text || "").trim();
        const oldText = node.text;
        if (!base) {
            return;
        }
        const newText = base + this.getEditableName(node).extension;
        if (newText === oldText) {
            return;
        }
        node.text = newText;
        try {
            await this.params.onRename(node, newText);
        } catch (error) {
            node.text = oldText;
            throw error;
        }
        this.getSiblings(node).sort(compareNodes);
        if (node.id === this.selectedId) {
            this.params.onSelect(node);
        }
    }

    /**
     * Rules for moving a node to another parent.
     *
     * @param {DmsTreeNode} node
     * @param {DmsTreeNode} parent
     * @returns {Boolean}
     */
    canMove(node, parent) {
        if (!node || !parent) {
            return false;
        }
        // Prevent moving a root node or a node to the root
        if (!node.parentId) {
            return false;
        }
        // Prevent moving a node to a storage or to a file
        if (parent.data?.resModel !== "dms.directory") {
            return false;
        }
        // Prevent moving a node to itself, its parent or its descendants
        if (
            parent.id === node.id ||
            parent.id === node.parentId ||
            this.isDescendant(parent, node)
        ) {
            return false;
        }
        return true;
    }

    /**
     * @param {DmsTreeNode} node
     */
    cut(node) {
        this.cutId = node.id;
    }

    /**
     * @param {DmsTreeNode} parent
     * @returns {Boolean}
     */
    canPaste(parent) {
        return this.canMove(this.cutNode, parent);
    }

    /**
     * Move the cut node into the given parent.
     *
     * @param {DmsTreeNode} parent
     */
    async paste(parent) {
        if (!this.canPaste(parent)) {
            return;
        }
        await this.move(this.cutNode, parent);
    }

    /**
     * Move the node into the given parent, without checking the rules.
     *
     * @param {DmsTreeNode} node
     * @param {DmsTreeNode} parent
     */
    async move(node, parent) {
        await this.params.onMove(node, parent);
        if (this.cutId === node.id) {
            this.cutId = null;
        }
        this.remove(node, {keepSelection: true});
        await this.reload(parent);
    }

    // -------------------------------------------------------------------------
    // Drag and drop
    // -------------------------------------------------------------------------

    /**
     * @param {DmsTreeNode} node
     * @returns {Boolean}
     */
    canDrag(node) {
        return (
            Boolean(node?.parentId) &&
            node.id !== this.renamingId &&
            this.params.canDrag(node)
        );
    }

    /**
     * @param {DmsTreeNode} node
     * @returns {Boolean} whether the drag has started
     */
    startDrag(node) {
        if (!this.canDrag(node)) {
            return false;
        }
        this.dragId = node.id;
        this.dropTargetId = null;
        return true;
    }

    endDrag() {
        this.dragId = null;
        this.dropTargetId = null;
    }

    /**
     * The folder that receives the dragged node when it is dropped over the
     * given node: the node itself if it is a folder, else its parent folder.
     *
     * @param {DmsTreeNode} node
     * @returns {DmsTreeNode|null}
     */
    getDropTarget(node) {
        const target =
            node?.data?.resModel === "dms.directory" ? node : this.getParent(node);
        const dragNode = this.dragNode;
        if (
            target &&
            this.canMove(dragNode, target) &&
            this.params.canDrop(dragNode, target)
        ) {
            return target;
        }
        return null;
    }

    /**
     * Update the highlighted folder while dragging over the given node.
     *
     * @param {DmsTreeNode|null} node
     * @returns {DmsTreeNode|null} the folder that would receive the node
     */
    dragOver(node) {
        const target = this.dragId && node ? this.getDropTarget(node) : null;
        this.dropTargetId = target?.id || null;
        return target;
    }

    /**
     * Move the dragged node into the folder of the given node.
     *
     * @param {DmsTreeNode} node
     */
    async drop(node) {
        const dragNode = this.dragNode;
        const target = this.getDropTarget(node);
        this.endDrag();
        if (dragNode && target) {
            await this.move(dragNode, target);
        }
    }

    /**
     * Remove the node from the tree (the record is not deleted).
     *
     * @param {DmsTreeNode} node
     * @param {Object} [options]
     * @param {Boolean} [options.keepSelection] do not unselect the node
     */
    remove(node, {keepSelection = false} = {}) {
        const removedIds = new Set(this.getAllNodes([node]).map((n) => n.id));
        const parent = this.getParent(node);
        const siblings = this.getSiblings(node);
        const index = siblings.findIndex((n) => n.id === node.id);
        if (index !== -1) {
            siblings.splice(index, 1);
        }
        if (parent) {
            parent.hasChildren = parent.children.length > 0;
            parent.isOpen = parent.isOpen && parent.hasChildren;
        }
        if (removedIds.has(this.cutId)) {
            this.cutId = null;
        }
        if (removedIds.has(this.renamingId)) {
            this.renamingId = null;
        }
        if (removedIds.has(this.dragId)) {
            this.endDrag();
        }
        if (removedIds.has(this.focusedId)) {
            this.focusedId = parent?.id || null;
        }
        if (!keepSelection && removedIds.has(this.selectedId)) {
            this.unselect();
        }
    }

    // -------------------------------------------------------------------------
    // Private
    // -------------------------------------------------------------------------

    /**
     * @param {DmsTreeNode} node
     */
    async _loadChildren(node) {
        node.isLoading = true;
        try {
            const rawNodes = await this.params.loadNodes(node);
            node.children = this._makeNodes(rawNodes, node.id);
            node.isLoaded = true;
            node.hasChildren = node.children.length > 0;
        } finally {
            node.isLoading = false;
        }
    }

    /**
     * @param {Object[]} rawNodes
     * @param {String|null} parentId
     * @returns {DmsTreeNode[]}
     */
    _makeNodes(rawNodes, parentId) {
        return (rawNodes || [])
            .map((rawNode) => this._makeNode(rawNode, parentId))
            .sort(compareNodes);
    }

    /**
     * @param {Object} rawNode
     * @param {String|null} parentId
     * @returns {DmsTreeNode}
     */
    _makeNode(rawNode, parentId) {
        const rawChildren = Array.isArray(rawNode.children) ? rawNode.children : null;
        return {
            id: rawNode.id,
            text: rawNode.text,
            type: rawNode.type,
            data: rawNode.data,
            parentId,
            children: rawChildren ? this._makeNodes(rawChildren, rawNode.id) : [],
            hasChildren: rawChildren
                ? rawChildren.length > 0
                : Boolean(rawNode.children),
            isLoaded: Boolean(rawChildren),
            isOpen: false,
            isLoading: false,
        };
    }

    /**
     * @param {DmsTreeNode[]} nodes
     * @returns {Set<String>}
     */
    _getOpenIds(nodes) {
        return new Set(
            this.getAllNodes(nodes)
                .filter((node) => node.isOpen)
                .map((node) => node.id)
        );
    }

    /**
     * @param {DmsTreeNode[]} nodes
     * @param {Set<String>} openIds
     */
    async _restoreOpen(nodes, openIds) {
        await Promise.all(
            nodes.map(async (node) => {
                if (!openIds.has(node.id)) {
                    return;
                }
                await this.open(node);
                await this._restoreOpen(node.children, openIds);
            })
        );
    }

    /**
     * Select again the node with the given id (its data may have changed), or
     * clear the selection if it is no longer in the tree.
     *
     * @param {String|null} selectedId
     */
    _restoreSelection(selectedId) {
        const node = this.findNode(selectedId);
        if (node) {
            this.selectedId = node.id;
            this.params.onSelect(node);
        } else if (this.selectedId || selectedId) {
            this.unselect();
        }
    }
}
