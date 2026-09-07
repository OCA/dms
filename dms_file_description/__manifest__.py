{
    "name": "DMS File Description",
    "summary": "Adds editable descriptions to DMS files and displays them in DMS views",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "category": "Document Management",
    "author": "Keith Brandenburg, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/dms",
    "depends": ["dms"],
    "data": [
        "views/dms_file_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "dms_file_description/static/src/scss/dms_file_description.scss",
        ],
    },
    "installable": True,
    "application": False,
}
