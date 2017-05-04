# -*- coding: utf-8 -*-

###################################################################################
# 
#    MuK Document Management System
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
    'name': "MuK Documents",
    'summary': """Document Management System""",
    'version': '1.0.0',   
    'category': 'Documents',   
    'license': 'AGPL-3',    
    'author': "MuK IT",
    'website': "http://www.mukit.at",
    'contributors': [
        "Mathias Markl <mathias.markl@mukit.at>",
        "Kerrim Abdelhamed <kerrim.adbelhamed@mukit.at>",
    ],
    'depends': [
        'base', 'web', 'mail', 'base_action_rule'
    ],
    'data': [
        'security/muk_dms_security.xml',
        'security/ir.model.access.csv',
        'views/muk_dms_view.xml',
        'views/muk_dms_view_tree.xml',
        'views/muk_dms_view_root.xml',
        'views/muk_dms_view_directory.xml',
        'views/muk_dms_view_file.xml',
        'views/muk_dms_view_data.xml',
        'views/muk_dms_view_lock.xml',
        'views/muk_dms_template_update.xml',
        'views/res_config.xml',
        'data/muk_dms_data.xml',
    ],
    'qweb': [
        'static/src/xml/*.xml'
    ],
    'demo': [
        'demo/muk_dms_demo_directory.xml',
        'demo/muk_dms_demo_root.xml',
        'demo/muk_dms_demo_file.xml',
    ],
    'images': [
        'static/description/banner.png'
    ],
    'installable': True,
    'application': True,
}
