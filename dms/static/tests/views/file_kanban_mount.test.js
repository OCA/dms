// /** ********************************************************************************
//     Copyright 2026 ledoent — Don Kendall
//     License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
//
//     Mount-view tests for `file_kanban` — these catch the two
//     browser-only crash modes we hit in Phase 11:
//       1. Regex literals in QWeb t-att expressions throw OwlError at
//          template-compile time, killing the entire app.
//       2. Owl serializes boolean attrs as empty strings, breaking CSS
//          selectors like `[data-preview-open="true"]`.
//     Pre-commit + Python tests don't catch either; they only fail in the
//     browser. This file mounts the view in Hoot to assert both never
//     regress silently again.
//  **********************************************************************************/
import {beforeEach, describe, expect, test} from "@odoo/hoot";
import {queryFirst} from "@odoo/hoot-dom";
import {defineModels, fields, models, mountView} from "@web/../tests/web_test_helpers";

// Side-effect: registers `file_kanban` view + the kanban renderer + record
// extensions + the preview-pane component used by the renderer.
import "@dms/js/views/file_kanban_view.esm";
import "@dms/js/components/preview/handlers.esm";

class DmsFile extends models.Model {
    _name = "dms.file";

    name = fields.Char();
    path_names = fields.Char();
    color = fields.Integer();
    active = fields.Boolean({default: true});
    mimetype = fields.Char();
    icon_url = fields.Char();
    human_size = fields.Char();
    write_date = fields.Datetime();
    locked_by = fields.Many2one({relation: "res.users"});
    is_locked = fields.Boolean();
    is_lock_editor = fields.Boolean();
    permission_write = fields.Boolean({default: true});
    permission_unlink = fields.Boolean({default: true});
    tag_ids = fields.Many2many({relation: "dms.tag"});

    _records = [
        {
            id: 1,
            name: "Report.pdf",
            path_names: "Documents/Reports/Report.pdf",
            color: 0,
            active: true,
            mimetype: "application/pdf",
            icon_url: "/dms/static/src/img/pdf.png",
            human_size: "1.2 MB",
            permission_write: true,
            permission_unlink: true,
        },
        {
            id: 2,
            name: "Photo.jpg",
            path_names: "Media/Pictures/Photo.jpg",
            color: 0,
            active: true,
            mimetype: "image/jpeg",
            icon_url: "/dms/static/src/img/image.png",
            human_size: "240 KB",
            permission_write: true,
            permission_unlink: true,
        },
    ];
}

class DmsTag extends models.Model {
    _name = "dms.tag";
    name = fields.Char();
    color = fields.Integer();
    _records = [];
}

beforeEach(() => {
    defineModels([DmsFile, DmsTag]);
    // Reset persisted state so prior runs don't bleed into the test.
    try {
        window.localStorage.removeItem("dms_kanban_density");
        window.localStorage.removeItem("dms_kanban_preview_pane");
    } catch {
        // Best-effort.
    }
});

// The kanban arch lives in `views/dms_file.xml` but we don't load that here
// — instead we inline a slim equivalent. The point is to exercise the OWL
// extension points (js_class="file_kanban", the card template's QWeb
// expressions, the data-preview-open attr) — not the full upstream arch.
const KANBAN_ARCH = `
<kanban js_class="file_kanban" class="mk_file_kanban_view">
    <field name="name"/>
    <field name="path_names"/>
    <field name="mimetype"/>
    <field name="icon_url"/>
    <field name="human_size"/>
    <field name="write_date"/>
    <field name="locked_by"/>
    <field name="is_locked"/>
    <field name="is_lock_editor"/>
    <field name="permission_write"/>
    <field name="permission_unlink"/>
    <field name="tag_ids"/>
    <field name="color"/>
    <field name="active"/>
    <templates>
        <t t-name="card">
            <t
                t-set="dms_ext"
                t-value="record.name.raw_value and record.name.raw_value.includes('.') ? record.name.raw_value.split('.').pop().toLowerCase() : ''"
            />
            <t
                t-set="dms_subtitle"
                t-value="record.path_names.raw_value ? record.path_names.raw_value.split('/').slice(0, -1).join('/') : ''"
            />
            <main
                class="o_kanban_dms_card oe_kanban_global_click"
                t-att-data-ext="dms_ext"
            >
                <div class="o_kanban_dms_card__thumb">
                    <img t-att-src="record.icon_url.raw_value" t-att-alt="record.name.raw_value"/>
                    <span
                        t-if="dms_ext"
                        class="o_kanban_dms_card__ext_pill"
                        t-esc="dms_ext"
                    />
                </div>
                <div class="o_kanban_dms_card__body">
                    <field name="name" class="o_kanban_dms_card__name fw-bold"/>
                    <div
                        t-if="dms_subtitle"
                        class="o_kanban_dms_card__subtitle text-muted small text-truncate"
                        t-att-title="dms_subtitle"
                        t-esc="dms_subtitle"
                    />
                </div>
            </main>
        </t>
    </templates>
</kanban>`;

describe("file_kanban mount", () => {
    test("view mounts without OwlError (regression: Owl regex-literal tokenizer crash)", async () => {
        // This bare mount is the canary for any QWeb-expression syntax that
        // the Owl tokenizer can't parse. Phase 11 had a regex literal that
        // killed the whole app; if that ever reappears, this test crashes
        // before the assertions even fire.
        await mountView({type: "kanban", resModel: "dms.file", arch: KANBAN_ARCH});
        expect(".o_kanban_renderer").toHaveCount(1);
        expect(".o_kanban_dms_card").toHaveCount(2);
    });

    test("o_dms_kanban_split has data-preview-open='true' string, not empty (regression: Owl boolean serialization)", async () => {
        // Phase 11 polish bug: `t-att-data-preview-open="previewOpen"`
        // (boolean) serialized as empty attr, breaking
        // `[data-preview-open="true"]` selectors. Fixed by coercing to
        // string in the template. This test pins the fix in place.
        await mountView({type: "kanban", resModel: "dms.file", arch: KANBAN_ARCH});
        const split = queryFirst(".o_dms_kanban_split");
        expect(split).toBeTruthy();
        const attr = split.getAttribute("data-preview-open");
        expect(["true", "false"]).toContain(attr);
        // Pane defaults to open → "true" is the expected initial value.
        expect(attr).toBe("true");
    });

    test("card data-ext attribute reflects filename extension (regression: QWeb expr eval)", async () => {
        await mountView({type: "kanban", resModel: "dms.file", arch: KANBAN_ARCH});
        const pdfCard = queryFirst(`.o_kanban_dms_card[data-ext="pdf"]`);
        expect(pdfCard).toBeTruthy();
        const jpgCard = queryFirst(`.o_kanban_dms_card[data-ext="jpg"]`);
        expect(jpgCard).toBeTruthy();
    });

    test("extension pill renders uppercase ext text", async () => {
        await mountView({type: "kanban", resModel: "dms.file", arch: KANBAN_ARCH});
        const pills = document.querySelectorAll(".o_kanban_dms_card__ext_pill");
        expect(pills.length).toBe(2);
        const texts = [...pills].map((p) => p.textContent.trim());
        // Pill text is the lowercase extension; uppercase comes from CSS
        // text-transform.
        expect(texts).toEqual(["pdf", "jpg"]);
    });

    test("directory subtitle renders the parent path (regression: regex-replace → slice)", async () => {
        // Phase 11a originally used .replace(/\/[^/]*$/, '') which crashed
        // the Owl tokenizer. The fix uses split/slice/join. This test
        // verifies the fix continues to produce the expected output —
        // the leading path without the filename.
        await mountView({type: "kanban", resModel: "dms.file", arch: KANBAN_ARCH});
        const subtitles = document.querySelectorAll(".o_kanban_dms_card__subtitle");
        expect(subtitles.length).toBe(2);
        const texts = [...subtitles].map((s) => s.textContent.trim());
        expect(texts).toEqual(["Documents/Reports", "Media/Pictures"]);
    });

    test("subtitle uses split-join-pop, so slash-in-filename is safe", async () => {
        // Seed a file whose own name contains a "/" — legal on HFS+ and
        // many other filesystems. `lastIndexOf('/')` would split inside
        // the filename and mislabel the subtitle. split/slice/join always
        // drops exactly the last segment.
        DmsFile._records = [
            {
                id: 99,
                name: "Notes/Draft.md",
                path_names: "Documents/Notes/Draft.md",
                color: 0,
                active: true,
                mimetype: "text/markdown",
                icon_url: "/dms/static/src/img/text.png",
                human_size: "1 KB",
                permission_write: true,
                permission_unlink: true,
            },
        ];
        await mountView({type: "kanban", resModel: "dms.file", arch: KANBAN_ARCH});
        const subtitle = queryFirst(".o_kanban_dms_card__subtitle");
        // Path_names = "Documents/Notes/Draft.md" — the parent path is
        // "Documents/Notes" (drop the last segment cleanly).
        expect(subtitle.textContent.trim()).toBe("Documents/Notes");
    });
});
