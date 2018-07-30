###################################################################################
# 
#    Copyright (C) 2017 MuK IT GmbH
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###################################################################################

{
    "name": "MuK Documents",
    "summary": """Document Management System""",
    "version": '11.0.2.1.6',   
    "category": 'Document Management',   
    "license": "AGPL-3",
    "website": "http://www.mukit.at",
    "live_test_url": "https://demo.mukit.at/web/login",
    "author": "MuK IT",
    "contributors": [
        "Mathias Markl <mathias.markl@mukit.at>",
    ],
    "depends": [
        "web",
        "mail",
        "base_setup",
        "muk_utils",
        "muk_security",
        "muk_web_utils",
        "muk_web_preview",
        "muk_web_client",
        "muk_web_client_refresh",
    ],
    "data": [
        "security/dms_security.xml",
        "security/ir.model.access.csv",
        "template/assets.xml",
        "views/dms_menu.xml",
        "views/dms_documents_view.xml",
        "views/dms_tag_view.xml",
        "views/dms_category_view.xml",
        "views/dms_settings_view.xml",
        "views/dms_directory_view.xml",
        "views/dms_file_view.xml",
        "views/dms_data_view.xml",
        "views/res_config_settings_view.xml",
    ],
    "demo": [
        "demo/dms_user_demo.xml",
        "demo/dms_tag_demo.xml",
        "demo/dms_category_demo.xml",
        "demo/dms_settings_demo.xml",
        "demo/dms_directory_demo.xml",
        "demo/dms_file_demo.xml",
    ],
    "qweb": [
        "static/src/xml/*.xml",
    ],
    "images": [
        'static/description/banner.png'
    ],
    "external_dependencies": {
        "python": [],
        "bin": [],
    },
    "application": True,
    "installable": True,
}