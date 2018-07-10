/**********************************************************************************
* 
*    Copyright (C) 2017 MuK IT GmbH
*
*    This program is free software: you can redistribute it and/or modify
*    it under the terms of the GNU Affero General Public License as
*    published by the Free Software Foundation, either version 3 of the
*    License, or (at your option) any later version.
*
*    This program is distributed in the hope that it will be useful,
*    but WITHOUT ANY WARRANTY; without even the implied warranty of
*    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
*    GNU Affero General Public License for more details.
*
*    You should have received a copy of the GNU Affero General Public License
*    along with this program.  If not, see <http://www.gnu.org/licenses/>.
*
**********************************************************************************/

odoo.define('muk_dms_views.DocumentsDialogController', function(require) {
"use strict";

var ajax = require('web.ajax');
var core = require('web.core');
var config = require('web.config');
var session = require('web.session');
var web_client = require('web.web_client');
var framework = require('web.framework');
var crash_manager = require('web.crash_manager');

var utils = require('muk_web_utils.common');
var mimetype = require('muk_web_utils.mimetype');

var DocumentsController = require('muk_dms_views.DocumentsController');

var _t = core._t;
var QWeb = core.qweb;

var DocumentsDialogController = DocumentsController.extend({
    _createDirecotry: function(node, name) {
		return this._rpc({
    		route: '/tree/create/directory',
    		params: {
    			name: name,
            	parent_directory: node.data.odoo_id,
            	context: _.extend({}, {
                	mail_create_nosubscribe: true,
                	mail_create_nolog: true,
                }, session.user_context),
            },
		});
    },
    _loadContextMenuDirectory: function($jstree, node, menu) {
    	var self = this;
    	menu = this._super($jstree, node, menu);
    	menu.create = {
			separator_before: false,
			separator_after: false,
			icon: "fa fa-plus",
			label: _t("Create"),
			action: false,
			submenu: {
				directory: {
					separator_before: false,
					separator_after: false,
					label: _t("Directory"),
					icon: "fa fa-folder-o",
					action: function(data) {
						function create() {
							self._createDirecotry(node).done(function(result) {
								$jstree.create_node(node, result, "last", function (new_node) {
									try {
										$jstree.edit(new_node);
									} catch (ex) {
										setTimeout(function () {
											$jstree.edit(new_node); 
										}, 0);
									}
								});
							}).fail(function() {
								self.do_warn(_t("Directory couldn't be created!"));
								self.refresh();
							});
						}
						if(!$jstree.is_open(node)) {
							$jstree.open_node(node, create);
						} else {
							create();
						}
					},
					_disabled: function (data) {
		    			return !node.data.perm_create;
	    			},
				},
			}	
		};
    	return menu;
    },
});

return DocumentsDialogController;

});