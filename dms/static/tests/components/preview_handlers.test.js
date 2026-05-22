// /** ********************************************************************************
//     Copyright 2026 ledoent — Don Kendall
//     License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
//
//     Verifies the built-in preview handlers:
//     - Per-mimetype getter URLs (src / downloadHref) are constructed
//       correctly so the rendered <img>/<iframe>/<audio>/<video> targets
//       the right /web/content endpoint
//     - Registry dispatch picks the right component for each mimetype family
//
//     The existing preview_registry.test.js covers the dispatch contract;
//     this file locks down the URL-builder contract per handler. Both layers
//     together protect downstream modules like dms_onlyoffice from silent
//     regressions in the seam between mimetype → component → URL.
//  **********************************************************************************/
import {describe, expect, test} from "@odoo/hoot";
import {
    AudioPreview,
    DownloadFallbackPreview,
    ImagePreview,
    MarkdownPreview,
    OfficeFallbackPreview,
    PdfPreview,
    TextPreview,
    VideoPreview,
} from "@dms/js/components/preview/handlers.esm";
import {getPreviewHandler} from "@dms/js/components/preview/preview_registry.esm";

function _component(Cls, file) {
    const inst = Object.create(Cls.prototype);
    inst.props = {file};
    return inst;
}

describe("ImagePreview", () => {
    test("src points to image_1920 endpoint on dms.file/<id>", () => {
        const c = _component(ImagePreview, {id: 42, name: "p.jpg"});
        expect(c.src).toBe("/web/image/dms.file/42/image_1920");
    });
});

describe("PdfPreview", () => {
    test("src includes write_date as cache buster (v=...)", () => {
        const c = _component(PdfPreview, {
            id: 7,
            name: "doc.pdf",
            write_date: "2026-05-22 09:00:00",
        });
        expect(c.src).toContain("/web/content?id=7&model=dms.file");
        expect(c.src).toContain("field=content");
        expect(c.src).toContain("v=2026-05-22");
    });

    test("src handles missing write_date gracefully (empty v=)", () => {
        const c = _component(PdfPreview, {id: 7, name: "doc.pdf"});
        expect(c.src).toContain("v=");
    });
});

describe("AudioPreview / VideoPreview", () => {
    test("audio src uses content endpoint without download flag", () => {
        const c = _component(AudioPreview, {id: 12, name: "song.mp3"});
        expect(c.src).toBe(
            "/web/content?id=12&model=dms.file&field=content&filename_field=name"
        );
    });

    test("video src matches the audio shape (same endpoint)", () => {
        const c = _component(VideoPreview, {id: 18, name: "clip.mp4"});
        expect(c.src).toBe(
            "/web/content?id=18&model=dms.file&field=content&filename_field=name"
        );
    });
});

describe("OfficeFallbackPreview", () => {
    test("downloadHref carries download=true + correct id", () => {
        const c = _component(OfficeFallbackPreview, {id: 5, name: "p.docx"});
        // QWeb-friendly &amp; in the URL — escaped because the same URL string
        // is rendered in an <a href> attribute via t-attf-href.
        expect(c.downloadHref).toContain("id=5");
        expect(c.downloadHref).toContain("download=true");
    });
});

describe("DownloadFallbackPreview", () => {
    test("downloadHref also carries download=true (catch-all)", () => {
        const c = _component(DownloadFallbackPreview, {id: 333, name: "f.bin"});
        expect(c.downloadHref).toContain("id=333");
        expect(c.downloadHref).toContain("download=true");
    });
});

describe("dispatch — built-in mimetype family routing", () => {
    test("application/pdf → PdfPreview", () => {
        const h = getPreviewHandler("application/pdf");
        expect(h.component).toBe(PdfPreview);
    });

    test("image/png → ImagePreview (image/* glob)", () => {
        const h = getPreviewHandler("image/png");
        expect(h.component).toBe(ImagePreview);
        expect(h.key).toBe("image/*");
    });

    test("audio/ogg → AudioPreview (audio/* glob)", () => {
        const h = getPreviewHandler("audio/ogg");
        expect(h.component).toBe(AudioPreview);
    });

    test("video/webm → VideoPreview (video/* glob)", () => {
        const h = getPreviewHandler("video/webm");
        expect(h.component).toBe(VideoPreview);
    });

    test("Word / OpenOffice mimetypes → OfficeFallbackPreview", () => {
        expect(getPreviewHandler("application/msword").component).toBe(
            OfficeFallbackPreview
        );
        expect(
            getPreviewHandler("application/vnd.oasis.opendocument.text").component
        ).toBe(OfficeFallbackPreview);
        expect(
            getPreviewHandler(
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            ).component
        ).toBe(OfficeFallbackPreview);
    });

    test("unknown binary → DownloadFallbackPreview (always-last fallback)", () => {
        const h = getPreviewHandler("application/x-binary-of-unknown-origin");
        expect(h.component).toBe(DownloadFallbackPreview);
        expect(h.score).toBe(-100);
    });

    test("text/plain → TextPreview (text/* glob)", () => {
        const h = getPreviewHandler("text/plain");
        expect(h.component).toBe(TextPreview);
    });

    test("text/markdown → MarkdownPreview (beats TextPreview at score 5)", () => {
        const h = getPreviewHandler("text/markdown");
        expect(h.component).toBe(MarkdownPreview);
        expect(h.score).toBe(5);
    });

    test("application/json → TextPreview (browser-readable application/*)", () => {
        const h = getPreviewHandler("application/json");
        expect(h.component).toBe(TextPreview);
    });
});
