// /** ********************************************************************************
//     Copyright 2026 ledoent — Don Kendall
//     License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
//
//     Locks down the dms.preview_handlers registry contract: built-in
//     handlers match the documented mimetypes, score ordering picks the
//     highest-scoring match, the catch-all download handler always wins
//     last. This is the seam dms_onlyoffice (and future preview extensions)
//     register against — regressions here silently break extension modules.
//  **********************************************************************************/

import {expect, test} from "@odoo/hoot";
import {
    getPreviewHandler,
    previewRegistry,
} from "@dms/js/components/preview/preview_registry.esm";

// Side-effect import: registers the built-in handlers.
import "@dms/js/components/preview/handlers.esm";

test("PDF mimetype resolves to the PDF handler", () => {
    const h = getPreviewHandler("application/pdf");
    expect(h).toBeTruthy();
    expect(h.key).toBe("application/pdf");
    expect(h.component).toBeTruthy();
});

test("image mimetypes match the image handler glob", () => {
    const h = getPreviewHandler("image/jpeg");
    expect(h).toBeTruthy();
    expect(h.key).toBe("image/*");
});

test("unknown mimetype falls back to the download handler", () => {
    const h = getPreviewHandler("application/x-unheard-of-format");
    expect(h).toBeTruthy();
    expect(h.key).toBe("__download__");
});

test("higher-scored handler beats built-in on the same mimetype", () => {
    // Simulate what dms_onlyoffice would do: register a score-10 handler
    // for application/msword. Verify the registry picks it over the
    // built-in OfficeFallback (score 0).
    const reg = previewRegistry();
    class FakeOnlyOfficePreview {}
    reg.add("test_onlyoffice", {
        component: FakeOnlyOfficePreview,
        match: (mt) => mt === "application/msword",
        score: 10,
    });
    try {
        const h = getPreviewHandler("application/msword");
        expect(h.component).toBe(FakeOnlyOfficePreview);
    } finally {
        reg.remove("test_onlyoffice");
    }
});

test("empty mimetype returns null (no false matches)", () => {
    expect(getPreviewHandler("")).toBe(null);
    expect(getPreviewHandler(null)).toBe(null);
    expect(getPreviewHandler(undefined)).toBe(null);
});
