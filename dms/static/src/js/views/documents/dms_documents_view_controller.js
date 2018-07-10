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

odoo.define('muk_dms_views.DocumentsViewController', function(require) {
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
var DocumentFileInfoDialog = require('muk_dms_dialogs.DocumentFileInfoDialog');
var DocumentDirectoryInfoDialog = require('muk_dms_dialogs.DocumentDirectoryInfoDialog');
var DocumentDropFileDialog = require('muk_dms_dialogs.DocumentDropFileDialog');
var DocumentDropFilesDialog = require('muk_dms_dialogs.DocumentDropFilesDialog');

var _t = core._t;
var QWeb = core.qweb;

var DocumentsViewController = DocumentsController.extend({
	_openInfo: function(node) {
		if(node.data.odoo_model == "muk_dms.file") {
			new DocumentFileInfoDialog(this, {
				id: node.data.odoo_id,
		    }).open();
    	} else {
    		new DocumentDirectoryInfoDialog(this, {
				id: node.data.odoo_id,
		    }).open();
    	}
    },
	_openNode: function(node) {
		var self = this;
		this.do_action({
    		type: 'ir.actions.act_window',
            res_model: node.data.odoo_model,
            res_id: node.data.odoo_id,
            views: [[false, 'form']],
            target: this.params.action_open_dialog ? 'new' : 'current',
            flags: {'form': {'initial_mode': 'readonly'}},
            context: session.user_context,
        }, {
            on_reverse_breadcrumb: function() {
            	self.trigger_up('reverse_breadcrumb', {});
            }
        });
    },
    _editNode: function(node) {
		var self = this;
    	this.do_action({
    		type: 'ir.actions.act_window',
            res_model: node.data.odoo_model,
            res_id: node.data.odoo_id,
            views: [[false, 'form']],
            target: this.params.action_open_dialog ? 'new' : 'current',
    	    flags: {'form': {'mode': 'edit', 'initial_mode': 'edit'}},
            context: session.user_context,
        }, {
            on_reverse_breadcrumb: function() {
            	self.trigger_up('reverse_breadcrumb', {});
            }
        });
    },
    _createNode: function(node, type) {
		var self = this;
    	var context = {};
    	if(type == "muk_dms.file") {
    		context = $.extend(session.user_context, {
    			default_directory: node.data.odoo_id
            });
    	} else if(type == "muk_dms.directory") {
    		context = $.extend(session.user_context, {
    			default_parent_directory: node.data.odoo_id
            });
    	}
    	this.do_action({
    		type: 'ir.actions.act_window',
            res_model: type,
            views: [[false, 'form']],
            target: this.params.action_open_dialog ? 'new' : 'current',
            flags: {'form': {'mode': 'edit', 'initial_mode': 'edit'}},
            context: session.user_context,
        }, {
            on_reverse_breadcrumb: function() {
            	self.trigger_up('reverse_breadcrumb', {});
            }
        });
    },
    _replaceFile: function(node) {
    	var self = this;
    	new DocumentDropFileDialog(this, {
			id: node.data.odoo_id,
			name: node.data.name,
			callback: function() {
				self.refreshParent(node);
			},
	    }).open();
    },
    _uploadFiles: function(node) {
    	var self = this;
    	new DocumentDropFilesDialog(this, {
			id: node.data.odoo_id,
			name: node.data.name,
			callback: function() {
				self.refreshNode(node);
			},
	    }).open();
    },
    _deleteNodes: function(nodes) {
    	var self = this;
    	var data = _.chain(nodes).map(function(node) {
    		return {model: node.data.odoo_model, id: node.data.odoo_id};
    	}).groupBy(function(tuple) {
    		return tuple.model;
    	}).value();
		data = _.mapObject(data, function(values, key) {
    		return _.map(values, function(value) {
    			return value.id;
    		});
    	});
		_.each(_.keys(data), function(key) {
			self._rpc({
	            model: key,
	            method: 'unlink',
	            args: [data[key]],
	            context: session.user_context,
			}).done(function() {
				self.do_notify(_t("The records have been deleted!"));
				self.refresh();
			}).fail(function() {
				self.refresh();
				self.do_warn(_t("The records couldn't be deleted!"));
			});
		});
    },
    _loadContextMenuBasic: function($jstree, node, menu) {
    	var self = this;
    	menu.info = {
			separator_before: false,
			separator_after: false,
			icon: "fa fa-info",
			label: _t("Info"),
			action: function (data) {
				self._openInfo(node);
			},
		};
    	menu.open = {
			separator_before: false,
			separator_after: false,
			icon: "fa fa-external-link",
			label: _t("Open"),
			action: function (data) {
				self._openNode(node);
			},
		};
    	menu.edit = {
			separator_before: false,
			separator_after: false,
			icon: "fa fa-pencil-square-o",
			label: _t("Edit"),
			action: function (data) {
				self._editNode(node);
			},
			_disabled: function (data) {
    			return !node.data.perm_write;
			},
		};
    	return this._super($jstree, node, menu);
    },
    _loadContextMenuDirectory: function($jstree, node, menu) {
    	var self = this;
    	menu = this._super($jstree, node, menu);
    	menu.upload = {
			separator_before: false,
			separator_after: false,
			icon: "fa fa-upload",
			label: _t("Upload"),
			action: function(data) {
				self._uploadFiles(node);
			},
	    	_disabled: function (data) {
				return !node.data.perm_create;
			},
    	};
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
						self._createNode(node, "muk_dms.directory");
					},
					_disabled: function (data) {
		    			return !node.data.perm_create;
	    			},
				},
				file : {
					separator_before: false,
					separator_after: false,
					label: _t("File"),
					icon: "fa fa-file-o",
					action: function(data) {
						self._createNode(node, "muk_dms.file");
					},
					_disabled: function (data) {
		    			return !node.data.perm_create;
	    			},
				},
			}	
		};
    	return menu;
    },
    _loadContextMenuFile: function($jstree, node, menu) {
    	var self = this;
    	menu.replace = {
			separator_before: false,
			separator_after: false,
			icon: "fa fa-retweet",
			label: _t("Replace"),
			action: function(data) {
				self._replaceFile(node);
			},
	    	_disabled: function (data) {
				return !node.data.perm_write;
			},
    	};
    	return this._super($jstree, node, menu);
    },
});

return DocumentsViewController;

});