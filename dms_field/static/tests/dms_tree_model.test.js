/* Copyright 2026 Tecnativa - Carlos Roca
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl). */
import {
    DmsTreeModel,
    compareNodes,
    splitFileName,
} from "@dms_field/components/dms_tree/dms_tree_model.esm";
import {describe, expect, test} from "@odoo/hoot";
import {proxy} from "@odoo/owl";

describe.current.tags("headless");

function dir(id, name, hasChildren = true) {
    return {
        id: `dms.directory_${id}`,
        text: name,
        type: "directory",
        data: {resModel: "dms.directory", data: {id, name}},
        children: hasChildren,
    };
}

function file(id, name) {
    return {
        id: `dms.file_${id}`,
        text: name,
        type: "file",
        data: {resModel: "dms.file", data: {id, name}},
        children: false,
    };
}

/**
 * Fake server: {parentNodeId: [raw nodes]}, "root" being the root nodes.
 * Children are copied on each load, like a server response.
 */
function makeModel(server, params = {}) {
    const loads = [];
    const model = proxy(
        new DmsTreeModel({
            loadNodes: async (node) => {
                const key = node ? node.id : "root";
                loads.push(key);
                return (server[key] || []).map((raw) => ({...raw}));
            },
            ...params,
        })
    );
    return {model, loads};
}

function names(nodes) {
    return nodes.map((node) => node.text);
}

const SERVER = {
    root: [dir(1, "Root")],
    "dms.directory_1": [
        file(10, "b.txt"),
        dir(2, "Zeta"),
        file(11, "a.txt"),
        dir(3, "Alpha"),
    ],
    "dms.directory_2": [file(20, "z.txt")],
    "dms.directory_3": [],
};

test("folders are sorted before files, then by name", () => {
    const nodes = [
        file(1, "b"),
        dir(2, "Z"),
        file(3, "a10"),
        file(4, "a9"),
        dir(5, "a"),
    ];
    expect(names(nodes.sort(compareNodes))).toEqual(["a", "Z", "a9", "a10", "b"]);
});

test("load fetches the roots and opens the whole tree", async () => {
    const {model, loads} = makeModel(SERVER);
    await model.load();
    const root = model.roots[0];
    expect(root.isOpen).toBe(true);
    expect(names(root.children)).toEqual(["Alpha", "Zeta", "a.txt", "b.txt"]);
    expect(model.findNode("dms.directory_2").isOpen).toBe(true);
    // A folder without children is not open and not expandable
    const alpha = model.findNode("dms.directory_3");
    expect(alpha.isOpen).toBe(false);
    expect(alpha.hasChildren).toBe(false);
    expect(loads.sort()).toEqual(
        ["dms.directory_1", "dms.directory_2", "dms.directory_3", "root"].sort()
    );
    expect(names(model.getVisibleNodes())).toEqual([
        "Root",
        "Alpha",
        "Zeta",
        "z.txt",
        "a.txt",
        "b.txt",
    ]);
});

test("closing a node hides its children and moves the focus to it", async () => {
    const {model} = makeModel(SERVER);
    await model.load();
    model.focus(model.findNode("dms.file_20"));
    model.close(model.findNode("dms.directory_2"));
    expect(model.focusedId).toBe("dms.directory_2");
    expect(names(model.getVisibleNodes())).not.toInclude("z.txt");
});

test("selection follows canSelect and notifies onSelect", async () => {
    const selected = [];
    const {model} = makeModel(SERVER, {
        canSelect: (node) => node.data.resModel === "dms.file",
        onSelect: (node) => selected.push(node && node.id),
    });
    await model.load();
    expect(model.select(model.findNode("dms.directory_2"))).toBe(false);
    expect(model.selectedId).toBe(null);
    expect(model.select(model.findNode("dms.file_20"))).toBe(true);
    expect(model.selectedId).toBe("dms.file_20");
    expect(selected).toEqual(["dms.file_20"]);
});

test("move rules", async () => {
    const {model} = makeModel(SERVER);
    await model.load();
    const root = model.findNode("dms.directory_1");
    const zeta = model.findNode("dms.directory_2");
    const alpha = model.findNode("dms.directory_3");
    const zFile = model.findNode("dms.file_20");
    const aFile = model.findNode("dms.file_11");
    // Root nodes can't be moved
    expect(model.canMove(root, zeta)).toBe(false);
    // Nodes can't be moved to a file
    expect(model.canMove(zFile, aFile)).toBe(false);
    // Nodes can't be moved to their current parent
    expect(model.canMove(zFile, zeta)).toBe(false);
    // Nodes can't be moved to themselves or their descendants
    expect(model.canMove(zeta, zeta)).toBe(false);
    expect(model.canMove(root, alpha)).toBe(false);
    // Valid moves
    expect(model.canMove(zFile, alpha)).toBe(true);
    expect(model.canMove(zeta, alpha)).toBe(true);
});

test("cut and paste moves the node and reloads the new parent", async () => {
    const server = structuredClone(SERVER);
    const {model} = makeModel(server, {
        onMove: async (node, parent) => {
            expect.step(`move ${node.id} to ${parent.id}`);
            // Simulate the write on the server
            server["dms.directory_2"] = server["dms.directory_2"].filter(
                (raw) => raw.id !== node.id
            );
            server[parent.id] = [...server[parent.id], file(20, "z.txt")];
        },
    });
    await model.load();
    model.select(model.findNode("dms.file_20"));
    model.cut(model.findNode("dms.file_20"));
    expect(model.canPaste(model.findNode("dms.directory_2"))).toBe(false);
    expect(model.canPaste(model.findNode("dms.directory_3"))).toBe(true);
    await model.paste(model.findNode("dms.directory_3"));
    expect.verifySteps(["move dms.file_20 to dms.directory_3"]);
    expect(model.cutId).toBe(null);
    const alpha = model.findNode("dms.directory_3");
    expect(alpha.isOpen).toBe(true);
    expect(names(alpha.children)).toEqual(["z.txt"]);
    expect(model.findNode("dms.directory_2").hasChildren).toBe(false);
    // The moved node keeps the selection
    expect(model.selectedId).toBe("dms.file_20");
});

test("rename trims the name, sorts again and reverts on error", async () => {
    let fail = false;
    const {model} = makeModel(SERVER, {
        onRename: async (node, text) => {
            expect.step(`rename ${node.id} ${text}`);
            if (fail) {
                throw new Error("Access error");
            }
        },
    });
    await model.load();
    const zeta = model.findNode("dms.directory_2");
    model.startRename(zeta);
    expect(model.renamingId).toBe("dms.directory_2");
    // Empty or unchanged names are ignored
    await model.rename(zeta, "   ");
    await model.rename(zeta, "Zeta");
    expect.verifySteps([]);
    expect(model.renamingId).toBe(null);
    await model.rename(zeta, "  Aaa  ");
    expect.verifySteps(["rename dms.directory_2 Aaa"]);
    expect(names(model.findNode("dms.directory_1").children)).toEqual([
        "Aaa",
        "Alpha",
        "a.txt",
        "b.txt",
    ]);
    fail = true;
    await expect(model.rename(zeta, "Other")).rejects.toThrow("Access error");
    expect.verifySteps(["rename dms.directory_2 Other"]);
    expect(zeta.text).toBe("Aaa");
});

test("reload keeps the open nodes", async () => {
    const server = structuredClone(SERVER);
    const {model} = makeModel(server);
    await model.load();
    model.close(model.findNode("dms.directory_2"));
    server["dms.directory_1"] = [...server["dms.directory_1"], dir(4, "New")];
    server["dms.directory_4"] = [file(40, "new.txt")];
    await model.reload(model.findNode("dms.directory_1"));
    expect(names(model.findNode("dms.directory_1").children)).toEqual([
        "Alpha",
        "New",
        "Zeta",
        "a.txt",
        "b.txt",
    ]);
    // Closed before the reload: it stays closed
    expect(model.findNode("dms.directory_2").isOpen).toBe(false);
    // New nodes are not opened
    expect(model.findNode("dms.directory_4").isOpen).toBe(false);
});

test("remove clears the state related to the removed nodes", async () => {
    const selected = [];
    const {model} = makeModel(SERVER, {
        onSelect: (node) => selected.push(node && node.id),
    });
    await model.load();
    model.select(model.findNode("dms.file_20"));
    model.cut(model.findNode("dms.file_20"));
    model.remove(model.findNode("dms.directory_2"));
    expect(model.findNode("dms.directory_2")).toBe(null);
    expect(model.selectedId).toBe(null);
    expect(model.cutId).toBe(null);
    expect(model.focusedId).toBe("dms.directory_1");
    expect(selected).toEqual(["dms.file_20", null]);
});

test("a stale load does not override a more recent one", async () => {
    const resolvers = [];
    const model = proxy(
        new DmsTreeModel({
            loadNodes: (node) =>
                node
                    ? Promise.resolve([])
                    : new Promise((resolve) => resolvers.push(resolve)),
        })
    );
    const first = model.load();
    const second = model.load();
    resolvers[1]([dir(2, "Second", false)]);
    await second;
    resolvers[0]([dir(1, "First", false)]);
    await first;
    expect(names(model.roots)).toEqual(["Second"]);
    expect(model.isLoading).toBe(false);
});

test("drag and drop moves the node into the folder of the drop target", async () => {
    const server = structuredClone(SERVER);
    const {model} = makeModel(server, {
        canDrag: (node) => node.id !== "dms.file_11",
        canDrop: (node, parent) => parent.id !== "dms.directory_1",
        onMove: async (node, parent) => {
            expect.step(`move ${node.id} to ${parent.id}`);
            server["dms.directory_1"] = server["dms.directory_1"].filter(
                (raw) => raw.id !== node.id
            );
            server[parent.id] = [...server[parent.id], file(10, "b.txt")];
        },
    });
    await model.load();
    // Root nodes and the nodes refused by canDrag can't be dragged
    expect(model.startDrag(model.findNode("dms.directory_1"))).toBe(false);
    expect(model.startDrag(model.findNode("dms.file_11"))).toBe(false);
    expect(model.dragId).toBe(null);

    expect(model.startDrag(model.findNode("dms.file_10"))).toBe(true);
    // Over a file: its folder is the target, unless it is the current one
    expect(model.dragOver(model.findNode("dms.file_20")).id).toBe("dms.directory_2");
    expect(model.dropTargetId).toBe("dms.directory_2");
    expect(model.dragOver(model.findNode("dms.file_11"))).toBe(null);
    expect(model.dropTargetId).toBe(null);
    // Refused by canDrop
    expect(model.getDropTarget(model.findNode("dms.directory_1"))).toBe(null);

    await model.drop(model.findNode("dms.file_20"));
    expect.verifySteps(["move dms.file_10 to dms.directory_2"]);
    expect(model.dragId).toBe(null);
    expect(model.dropTargetId).toBe(null);
    expect(names(model.findNode("dms.directory_2").children)).toEqual([
        "b.txt",
        "z.txt",
    ]);
    expect(names(model.findNode("dms.directory_1").children)).not.toInclude("b.txt");
});

test("dropping on an invalid target does nothing", async () => {
    const {model} = makeModel(SERVER, {
        onMove: async () => expect.step("move"),
    });
    await model.load();
    model.startDrag(model.findNode("dms.directory_2"));
    // A folder can't be moved into itself or its descendants
    await model.drop(model.findNode("dms.file_20"));
    expect.verifySteps([]);
    expect(model.dragId).toBe(null);
    expect(model.findNode("dms.directory_2").parentId).toBe("dms.directory_1");
});

test("file names are split like os.path.splitext", () => {
    const split = (name) => Object.values(splitFileName(name));
    expect(split("report.pdf")).toEqual(["report", ".pdf"]);
    expect(split("report.final.PDF")).toEqual(["report.final", ".PDF"]);
    expect(split("README")).toEqual(["README", ""]);
    expect(split(".bashrc")).toEqual([".bashrc", ""]);
    expect(split("..hidden")).toEqual(["..hidden", ""]);
    expect(split(".config.json")).toEqual([".config", ".json"]);
});

test("renaming a file keeps its extension", async () => {
    const server = structuredClone(SERVER);
    server["dms.directory_1"].push(file(12, "README"));
    const {model} = makeModel(server, {
        onRename: async (node, text) => expect.step(`rename ${node.id} ${text}`),
    });
    await model.load();
    const bFile = model.findNode("dms.file_10");
    expect(model.getEditableName(bFile)).toEqual({base: "b", extension: ".txt"});
    // Folders are renamed as a whole
    expect(model.getEditableName(model.findNode("dms.directory_2"))).toEqual({
        base: "Zeta",
        extension: "",
    });
    // Unchanged or empty base names are ignored
    await model.rename(bFile, " b ");
    await model.rename(bFile, "  ");
    expect.verifySteps([]);
    // A typed extension is part of the base name
    await model.rename(bFile, "c.pdf");
    expect.verifySteps(["rename dms.file_10 c.pdf.txt"]);
    expect(bFile.text).toBe("c.pdf.txt");
    // Files without extension
    await model.rename(model.findNode("dms.file_12"), "LICENSE");
    expect.verifySteps(["rename dms.file_12 LICENSE"]);
});
