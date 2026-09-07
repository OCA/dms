{
    "name": "DMS Field File Description Preview",
    "summary": "Shows DMS file descriptions in embedded DMS preview panes",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "category": "Document Management",
    "author": "Keith Brandenburg, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/dms",
    "depends": ["dms_field", "dms_file_description"],
    "assets": {
        "web.assets_backend": [
            "dms_field_file_description_preview/static/src/js/"
            "dms_document_preview_description.esm.js",
            "dms_field_file_description_preview/static/src/scss/"
            "dms_field_file_description_preview.scss",
        ],
    },
    "auto_install": True,
    "installable": True,
    "application": False,
}
