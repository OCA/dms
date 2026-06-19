// /** ********************************************************************************
//     Copyright 2026 ledoent — Don Kendall
//     License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
//
//     Pins the registration contract: every office mimetype the Python
//     OFFICE_MIMETYPES set knows how to convert MUST resolve to
//     LibreofficePreview at the score that beats the OfficeFallbackPreview
//     shipped in base dms. If this test fires, the side-pane will silently
//     drop back to the download card and users will get a non-working
//     "Download" affordance instead of an inline PDF render.
//  **********************************************************************************/
import {describe, expect, test} from "@odoo/hoot";
import {LibreofficePreview} from "@dms_libreoffice_preview/js/libreoffice_preview.esm";
import {getPreviewHandler} from "@dms_preview_pane/js/components/preview/preview_registry.esm";

const OFFICE_MIMETYPES = [
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.oasis.opendocument.text",
    "application/rtf",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.oasis.opendocument.spreadsheet",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.oasis.opendocument.presentation",
];

describe("LibreofficePreview registry binding", () => {
    test("every supported office mimetype routes to LibreofficePreview", () => {
        for (const mt of OFFICE_MIMETYPES) {
            const h = getPreviewHandler(mt);
            expect(h.component).toBe(LibreofficePreview);
            // Beats the score-0 OfficeFallbackPreview in base dms.
            expect(h.score).toBe(10);
        }
    });

    test("non-office mimetype does NOT match this handler", () => {
        const h = getPreviewHandler("image/png");
        expect(h.component).not.toBe(LibreofficePreview);
    });
});

describe("LibreofficePreview.src", () => {
    test("src points to /dms/file/<id>/libreoffice_preview with cache buster", () => {
        const inst = Object.create(LibreofficePreview.prototype);
        inst.props = {
            file: {id: 42, name: "p.docx", write_date: "2026-05-22 09:00:00"},
        };
        expect(inst.src).toMatch("/dms/file/42/libreoffice_preview");
        expect(inst.src).toMatch("v=2026-05-22");
    });

    test("missing write_date still produces a valid URL", () => {
        const inst = Object.create(LibreofficePreview.prototype);
        inst.props = {file: {id: 7, name: "x.odt"}};
        expect(inst.src).toMatch("/dms/file/7/libreoffice_preview?v=");
    });
});
