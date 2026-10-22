// /** ********************************************************************************
//     Copyright 2026 ledoent — Don Kendall
//     License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
//
//     Verifies the FilePreviewPane component's behavior contract:
//     - State machine (empty, loading, loaded, error)
//     - ORM read shape (correct model + fields)
//     - Handler dispatch via the preview registry
//     - Action toolbar actions (Download URL, Share + Open form dispatch)
//
//     Mounted-component coverage is left to the directory kanban + list
//     renderer integration tests; this file asserts on the pure-logic
//     methods using a stand-in instance.
//  **********************************************************************************/
import {describe, expect, test} from "@odoo/hoot";
import {
    getPreviewHandler,
    previewRegistry,
} from "@dms_preview_pane/js/components/preview/preview_registry.esm";
import {FilePreviewPane} from "@dms_preview_pane/js/components/preview/file_preview_pane.esm";

// Stand-in: bypass setup() so we don't need a mounted env. Plain reactive-
// shaped state object is enough for the assertions below.
function _instance({state = {}, orm = null, action = null, onClose = null} = {}) {
    const inst = Object.create(FilePreviewPane.prototype);
    inst.state = {loading: false, file: null, error: null, ...state};
    inst.orm = orm;
    inst.action = action;
    inst.props = {recordId: null, onClose};
    return inst;
}

describe("_load — ORM contract", () => {
    test("calls orm.read with the correct model + field list", async () => {
        const calls = [];
        const orm = {
            read: async (model, ids, fields) => {
                calls.push({model, ids, fields});
                return [{id: 42, name: "f.pdf", mimetype: "application/pdf"}];
            },
        };
        const inst = _instance({orm});
        await inst._load(42);
        expect(calls.length).toBe(1);
        expect(calls[0].model).toBe("dms.file");
        expect(calls[0].ids).toEqual([42]);
        // Read fields must include the keys the header + empty-state copy
        // depend on. Assert inclusion, not an exact list: feature work (the
        // Details tab, icon_url, …) legitimately adds fields — that's fine;
        // only removing a core key should break this.
        for (const field of ["id", "name", "mimetype", "write_date", "human_size"]) {
            expect(calls[0].fields).toInclude(field);
        }
    });

    test("populates state.file on success + clears loading", async () => {
        const orm = {
            read: async () => [{id: 7, name: "doc.pdf", mimetype: "application/pdf"}],
        };
        const inst = _instance({orm});
        await inst._load(7);
        expect(inst.state.loading).toBe(false);
        expect(inst.state.file.id).toBe(7);
        expect(inst.state.error).toBe(null);
    });

    test("populates state.error on failure + clears file", async () => {
        const orm = {
            read: async () => {
                throw new Error("AccessError: not allowed");
            },
        };
        const inst = _instance({state: {file: {id: 1}}, orm});
        await inst._load(99);
        expect(inst.state.loading).toBe(false);
        expect(inst.state.file).toBe(null);
        expect(inst.state.error).toInclude("AccessError");
    });
});

describe("handler dispatch via registry", () => {
    test("returns null when no file is loaded", () => {
        const inst = _instance();
        expect(inst.handler).toBe(null);
        expect(inst.HandlerComponent).toBe(null);
    });

    test("delegates to getPreviewHandler when file is loaded", () => {
        // Register a stub handler scoped to a synthetic mimetype so we
        // never collide with the built-in dispatcher set.
        class StubPreviewComponent {}
        const stubComponent = StubPreviewComponent;
        const reg = previewRegistry();
        reg.add("test_pane_stub", {
            component: stubComponent,
            match: (mt) => mt === "application/x-dms-test",
            score: 100,
        });
        try {
            const inst = _instance({
                state: {file: {id: 1, mimetype: "application/x-dms-test"}},
            });
            const handler = inst.handler;
            expect(handler?.key).toBe("test_pane_stub");
            expect(inst.HandlerComponent).toBe(stubComponent);
            // The registry returned the same handler the pane resolved to —
            // proves the pane delegates rather than caching its own copy.
            expect(getPreviewHandler("application/x-dms-test")?.key).toBe(
                "test_pane_stub"
            );
        } finally {
            reg.remove("test_pane_stub");
        }
    });
});

describe("toolbar actions", () => {
    test("onDownloadClick is a no-op when no file loaded", () => {
        const inst = _instance();
        let opened = null;
        const origOpen = window.open;
        window.open = (url) => {
            opened = url;
        };
        try {
            inst.onDownloadClick();
            expect(opened).toBe(null);
        } finally {
            window.open = origOpen;
        }
    });

    test("onDownloadClick opens the /web/content URL with download=true", () => {
        const inst = _instance({state: {file: {id: 42, name: "f.pdf"}}});
        let openedUrl = null;
        let openedTarget = null;
        const origOpen = window.open;
        window.open = (url, target) => {
            openedUrl = url;
            openedTarget = target;
        };
        try {
            inst.onDownloadClick();
            expect(openedUrl).toInclude("/web/content?model=dms.file&id=42");
            expect(openedUrl).toInclude("download=true");
            expect(openedUrl).toInclude("filename_field=name");
            expect(openedTarget).toBe("_blank");
        } finally {
            window.open = origOpen;
        }
    });

    test("onShareClick dispatches the share action with active_* context", async () => {
        const dispatched = [];
        const action = {
            doAction: async (xmlid, opts) => dispatched.push({xmlid, opts}),
        };
        const inst = _instance({state: {file: {id: 7}}, action});
        await inst.onShareClick();
        expect(dispatched.length).toBe(1);
        expect(dispatched[0].xmlid).toBe("dms.wizard_dms_file_share_action");
        // Wizard inherits portal.share — reads active_model + active_ids from
        // context to seed res_model + res_id. Don't lose this contract.
        expect(dispatched[0].opts.additionalContext.active_model).toBe("dms.file");
        expect(dispatched[0].opts.additionalContext.active_ids).toEqual([7]);
        expect(dispatched[0].opts.additionalContext.active_id).toBe(7);
    });

    test("onOpenFormClick dispatches the file action in form viewType", async () => {
        const dispatched = [];
        const action = {
            doAction: async (xmlid, opts) => dispatched.push({xmlid, opts}),
        };
        const inst = _instance({state: {file: {id: 33}}, action});
        await inst.onOpenFormClick();
        expect(dispatched.length).toBe(1);
        expect(dispatched[0].xmlid).toBe("dms.action_dms_file");
        expect(dispatched[0].opts.viewType).toBe("form");
        // Plain action descriptor lost the action context — must pass via
        // props.resId for breadcrumbs to render correctly. Regression-prone.
        expect(dispatched[0].opts.props.resId).toBe(33);
    });

    test("toolbar actions are no-ops when no file loaded", async () => {
        const dispatched = [];
        const action = {doAction: async (...args) => dispatched.push(args)};
        const inst = _instance({action});
        await inst.onShareClick();
        await inst.onOpenFormClick();
        expect(dispatched.length).toBe(0);
    });
});

describe("close callback", () => {
    test("onCloseClick invokes the onClose prop callback", () => {
        let called = false;
        const inst = _instance({onClose: () => (called = true)});
        inst.onCloseClick();
        expect(called).toBe(true);
    });

    test("onCloseClick is safe when no onClose prop provided", () => {
        const inst = _instance();
        expect(() => inst.onCloseClick()).not.toThrow();
    });
});

describe("handler dispatch with effective-mimetype fallback", () => {
    // The pane's `handler` getter feeds the file through `_effectiveMimetype`
    // before asking the registry — falling back on the filename extension
    // when the stored mimetype is generic (libmagic returns
    // application/octet-stream for several MP4 container variants).
    test("application/octet-stream + .mp4 name → routes via video/mp4", () => {
        const inst = _instance({
            state: {
                file: {
                    id: 1,
                    name: "Movie.mp4",
                    mimetype: "application/octet-stream",
                },
            },
        });
        // Resolves to the VideoPreview handler registered for video/* —
        // the extension fallback rescued it from DownloadFallbackPreview.
        expect(inst.handler).not.toBe(null);
        expect(inst.handler.key).toBe("video/*");
    });

    test("crisp mimetype is preferred over extension fallback", () => {
        // Application/pdf takes precedence even if the filename has a
        // misleading extension — the stored mimetype is authoritative
        // unless it's generic.
        const inst = _instance({
            state: {
                file: {id: 2, name: "weird.mp4", mimetype: "application/pdf"},
            },
        });
        expect(inst.handler.key).toBe("application/pdf");
    });

    test("application/octet-stream with no extension → download fallback", () => {
        const inst = _instance({
            state: {
                file: {
                    id: 3,
                    name: "unknown",
                    mimetype: "application/octet-stream",
                },
            },
        });
        // No `.` in name → split-on-dot returns the whole name, no mapping
        // hit → fall through to the score=-100 generic fallback.
        expect(inst.handler.score).toBe(-100);
    });

    test(".md name with octet-stream mimetype routes to text/markdown", () => {
        const inst = _instance({
            state: {
                file: {
                    id: 4,
                    name: "Notes.md",
                    mimetype: "application/octet-stream",
                },
            },
        });
        expect(inst.handler.key).toBe("text/markdown");
    });

    test("source-code extension routes to the code-editor handler", () => {
        // .py stored as the generic text/plain → _effectiveMimetype rewrites
        // it to text/x-python → CodePreview wins over the plain text iframe.
        const inst = _instance({
            state: {file: {id: 8, name: "build.py", mimetype: "text/plain"}},
        });
        expect(inst.handler.key).toBe("text/code");
    });

    test("plain text with no code extension stays on the text iframe", () => {
        // .rst has no bundled ACE mode and no code-mimetype mapping — it must
        // not get hijacked by CodePreview; the browser renders it fine.
        const inst = _instance({
            state: {file: {id: 9, name: "notes.rst", mimetype: "text/plain"}},
        });
        expect(inst.handler.key).toBe("text/*");
    });

    test("audio/video extension wins over a wrong image/* mimetype", () => {
        // The OCA dms demo stores .wav files as image/webp (a thumbnail type
        // leaking onto media). An image mimetype on a known audio/video
        // extension is never right → trust the extension so it plays.
        const wav = _instance({
            state: {file: {id: 5, name: "Loop_01.wav", mimetype: "image/webp"}},
        });
        expect(wav.handler.key).toBe("audio/*");
        const mp4 = _instance({
            state: {file: {id: 6, name: "Clip.mp4", mimetype: "image/png"}},
        });
        expect(mp4.handler.key).toBe("video/*");
        // …but a genuine image keeps its image preview (no false override).
        const png = _instance({
            state: {file: {id: 7, name: "Logo.png", mimetype: "image/png"}},
        });
        expect(png.handler.key).toBe("image/*");
    });
});
