# Copyright 2026 ledoent — Don Kendall
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "DMS — LibreOffice Preview",
    "summary": (
        "In-browser preview of office files in DMS via "
        "server-side LibreOffice→PDF conversion"
    ),
    "version": "19.0.1.0.0",
    "category": "Document Management",
    "license": "LGPL-3",
    "website": "https://github.com/OCA/dms",
    "author": "ledoent, Odoo Community Association (OCA)",
    "maintainers": ["dnplkndll"],
    "depends": ["dms", "dms_preview_pane"],
    "external_dependencies": {
        "deb": ["libreoffice", "fonts-noto", "fonts-liberation"],
    },
    "assets": {
        "web.assets_backend": [
            "dms_libreoffice_preview/static/src/js/libreoffice_preview.esm.js",
            "dms_libreoffice_preview/static/src/js/libreoffice_preview.xml",
        ],
        "web.assets_unit_tests": [
            "dms_libreoffice_preview/static/tests/**/*.test.js",
        ],
    },
    "installable": True,
}
