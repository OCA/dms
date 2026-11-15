# Copyright 2026 ledoent - Don Kendall
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
{
    "name": "DMS Preview Pane",
    "summary": "Side-by-side file preview pane for the DMS list & kanban views",
    "version": "19.0.1.0.0",
    "category": "Document Management",
    "license": "LGPL-3",
    "website": "https://github.com/OCA/dms",
    "author": "ledoent, Odoo Community Association (OCA)",
    "maintainers": ["dnplkndll"],
    "depends": ["dms"],
    "assets": {
        "web.assets_backend": [
            "dms_preview_pane/static/src/js/utils/storage.esm.js",
            "dms_preview_pane/static/src/js/utils/use_stored_state.esm.js",
            "dms_preview_pane/static/src/js/components/preview/preview_registry.esm.js",
            "dms_preview_pane/static/src/js/components/preview/handlers.esm.js",
            "dms_preview_pane/static/src/js/components/preview/handlers.xml",
            "dms_preview_pane/static/src/js/components/preview/file_preview_pane.esm.js",
            "dms_preview_pane/static/src/js/components/preview/file_preview_pane.xml",
            "dms_preview_pane/static/src/js/file_list_renderer_patch.esm.js",
            "dms_preview_pane/static/src/js/file_list_renderer_patch.xml",
            "dms_preview_pane/static/src/js/file_kanban_renderer_patch.esm.js",
            "dms_preview_pane/static/src/js/file_kanban_renderer_patch.xml",
            "dms_preview_pane/static/src/scss/file_preview_pane.scss",
        ],
        "web.assets_unit_tests": [
            "dms_preview_pane/static/tests/**/*.test.js",
        ],
    },
}
