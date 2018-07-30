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

odoo.define('muk_dms_views.DocumentsController', function(require) {
"use strict";

var ajax = require('web.ajax');
var core = require('web.core');
var mixins = require('web.mixins');
var config = require('web.config');
var session = require('web.session');
var framework = require('web.framework');
var web_client = require('web.web_client');
var fieldUtils = require('web.field_utils');
var crash_manager = require('web.crash_manager');

var utils = require('muk_web_utils.common');
var files = require('muk_web_utils.files');
var mimetype = require('muk_web_utils.mimetype');

var Widget = require('web.Widget');

var _t = core._t;
var QWeb = core.qweb;

var message = _.template("<%= progress %> / <%= total %>");

var DocumentsController = Widget.extend({
    custom_events: _.extend({}, Widget.prototype.custom_events, {
    	drop_items: '_dropItems',
    	tree_changed: '_treeChanged',
    	move_node: '_moveNode',
    	copy_node: '_copyNode',
    	rename_node: '_renameNode',
    	delete_node: '_deleteNode',
    }),
	init: function (parent, model, renderer, params) {
        this._super.apply(this, arguments);
        this.params = params || {};
        this.config = this._buildTreeConfig();
        this.model = new model(this, _.extend({}, params.model, {}));
        this.renderer = new renderer(this, _.extend({}, params.render, {
        	dnd: params.dnd,
        	config: this.config,
        }));
        this.FileReaderAPI = window.File && window.FileReader && window.FileList && window.Blob;
        this.searchTester = new RegExp(/\%|\_/);
    },
    start: function () {
        return $.when(
            this._super.apply(this, arguments),
            this.renderer.appendTo(this.$el)
        );
    },
    refresh: function(message) {
    	var jstree = this.renderer.$tree.jstree(true);
    	if(message && message.ids && message.model && !message.create) {
    		var nodes = _.each(_.keys(_.chain(message.ids).map(function(id) {
	    		return jstree.get_parent(message.model.split(".")[1] + "_" + id);
	    	}).filter(function(parent) {
	    		return !!parent;
	    	}).groupBy(function(parent) {
	    		return parent;
	    	}).value()), function(node, index, nodes) {
    			if(message.model === 'muk_dms.directory') {
    				node = jstree.get_parent(node);
    			}
    			jstree.refresh_node(node);
    		});
    	} else if(message && message.ids && message.model && message.create) {
    		var id = message.ids && message.ids.length > 0 ? message.ids[0] : false;
    		if(id && message.model) {
    			var field = message.model === 'muk_dms.directory' ? 'parent_directory' : 'directory';
    			this._rpc({
    				 fields: [field],
    				 domain: [['id', '=', id]],
    				 model: message.model,
    				 method: 'search_read',
    				 context: session.user_context,
    			}).then(function(records) {
    				var record = records.length > 0 && records[0];
    				jstree.refresh_node(message.model.split(".")[1] + "_" + record[field][0]);
    			});
    		}
    	} else {
    		jstree.refresh();
    	}
    },
    refreshNode: _.memoizeDebounce(function(node) {
    	this.renderer.$tree.jstree(true).refresh_node(node);
    }, 250),
    refreshParent: _.memoizeDebounce(function(node) {
    	var jstree = this.renderer.$tree.jstree(true);
    	var parent = jstree.get_parent(node);
    	if(parent) {
    		this.renderer.$tree.jstree(true).refresh_node(parent);
    	} else {
    		this.refreshNode(node);
    	}
    }, 250),
    search: function(val, node) {
    	this.renderer.$tree.jstree(true).search(val, false, this.params.show_only_matches || true, node);
    },
    getSelectedItem: function() {
    	var jstree = this.renderer.$tree.jstree(true);
    	var selected = jstree.get_selected();
		return selected.length > 0 ? jstree.get_node(selected[0]) : false;
    },
    getTopSelectedItem: function() {
    	var jstree = this.renderer.$tree.jstree(true);
    	var selected = jstree.get_top_selected();
    	return selected.length > 0 ? jstree.get_node(selected[0]) : false;
    },
    getSelectedDirectory: function() {
    	var jstree = this.renderer.$tree.jstree(true);
    	var selected = jstree.get_top_selected(true);
    	var directories = _.filter(selected, function(node) {
    		return node.data.odoo_model === "muk_dms.directory";
    	});
    	if(directories.length > 0) {
    		return directories[0];
    	} else if(selected.length > 0) {
    		return jstree.get_node(jstree.get_parent(selected[0]));
    	} else {
    		return false;
    	}
    },
    getParentNode: function(node) {
    	var jstree = this.renderer.$tree.jstree(true);
    	return jstree.get_node(jstree.get_parent(node));
    },
    getSelectedItems: function() {
    	return this.renderer.$tree.jstree(true).get_selected(true);
    },
    getTopSelectedItems: function() {
    	return this.renderer.$tree.jstree(true).get_top_selected(true);
    },
    _buildTreeConfig: function() {
		var self = this;
		var plugins = this.params.plugins || [
			"conditionalselect", "massload", "wholerow", "state", "sort", "search", "types"
		];
		if(this.params.dnd) {
			plugins = _.union(plugins, ["dnd"]);
		}
		if(this.params.contextmenu) {
			plugins = _.union(plugins, ["contextmenu"]);
		}
		var config = {
        	core : {
        		widget: this,
        		animation: this.params.animation || 0,
        		multiple: this.params.disable_multiple ? false : true,
        	    check_callback: this.params.check_callback || this._checkCallback.bind(this),
        		themes: this.params.themes || {
                    name: 'proton',
                    responsive: true
                },
        		data: this._loadData.bind(this),
        	},
        	massload: this._massloadData.bind(this),
        	contextmenu: this.params.contextmenu_items || { 
        		items: this._loadContextMenu.bind(this),
        	},
            search: this.params.search || {
            	ajax: this._searchData.bind(this),
            	show_only_matches: true,
            	search_callback: this._searchCallback.bind(this),
            },
        	state : {
        		key: this.params.key || "documents" 
        	},
        	conditionalselect: this.params.conditionalselect || this._checkSelect.bind(this),
        	dnd: this.params.dnd_options || {
        		touch: false,
        	},
	        plugins: plugins,
    	};
		return config;
    },
    _checkCallback: function (operation, node, parent, position, more) {
    	if(operation === "copy_node" || operation === "move_node") {
    		// prevent moving a root node
    		if(node.parent === "#") {
    			return false;
            }
    		// prevent moving a child above or below the root
    		if(parent.id === "#") {
    			return false;
	        }
    		// prevent moving a child to a settings object
    		if(parent.data && parent.data.odoo_model === "muk_dms.settings") {
    			return false;
            }
    		// prevent moving a child to a file
    		if(parent.data && parent.data.odoo_model === "muk_dms.file") {
    			return false;
            }
    	}
    	if(operation === "move_node") {
    		// prevent duplicate names
    		if(node.data && parent.data) {
    			var names = [];
    			var jstree = this.renderer.$tree.jstree(true);
    			_.each(parent.children, function(child, index, children) {
    				var child_node = jstree.get_node(child);
    				if(child_node.data && child_node.data.odoo_model === parent.data.odoo_model) {
    					names.push(child_node.data.name);
    				}
    			});
    			if(names.indexOf(node.data.name) > -1) {
    				return false;
    			}
            }
        }
    	return true;
    },
    _checkSelect: function(node, event) {
    	if(this.params.filesOnly && node.data.odoo_model !== "muk_dms.file") {
    		return false;
    	}
    	return !(node.parent === '#' && node.data.odoo_model === "muk_dms.settings");
    },
    _treeChanged: function(ev) {
    	$("#menuContinenti").prop('disabled', function (_, val) { return ! val; });
    },
    _loadData: function (node, callback) {
    	this.model.load(node).then(function(data) {
			callback.call(this, data);
		});
    },
    _massloadData: function (data, callback) {
    	this.model.massload(data).then(function(data) {
			callback.call(this, data);
		});
    },
    _searchData: function(val, node, callback) {
    	node = node || this.getSelectedDirectory();
    	if(node) {
	    	this.model.search(val, node, {
	    		search: {
	    			operator: this.searchTester.test(val) ? "=ilike" : "ilike",
	    		}
	    	}).then(function(data) {
				callback.call(this, data);
			});
    	} else {
    		callback.call(this, []);
    	}
    },
    _searchCallback: function (val, node) {
    	if(this.searchTester.test(val)) {
    		var regex = new RegExp(val.replace(/\%/g, ".*").replace(/\_/g, "."), "i");
        	try {
        		return regex.test(node.text); 
        	} catch(ex) {
        		return false; 
        	} 
    	} else {
    		var lval = val.toLowerCase();
    		var ltext = node.text.toLowerCase();
    		if(lval === ltext || ltext.indexOf(lval) !== -1) {
    			return true;
    		} else {
    			return false;
    		}
    	}
    },
    _dropItems: function(ev) {
    	var self = this;
    	var items = ev.data.items;
    	var node = this.getSelectedDirectory();
    	if(node) {
    		files.get_file_structure(items).then(function(structure) {
    			var $finished = $.Deferred();
    			var steps = files.count_files_in_structure(structure);
    			var progress = steps;
    			var $notify = $.notify({
    				title: _t('<strong>Progress</strong>'),
    				message: message({progress: 0, total: steps}),
    				progress: 0,
    			}, {
    				type: 'info',
    				allow_dismiss: false,
    				showProgressbar: true,
    				placement: {
    					from: "bottom",
    					align: "right"
    				},
    				offset: {
    					x: 30,
    					y: 20
    				}
    			});
				function create(item, parent) {
					if(item.isFile || item.isFileItem) {
						files.read_file(item, function (upload) {
							var data = upload.target.result;
						    data = data.split(',')[1];
						    self._rpc({
						    	model: 'muk_dms.file',
		    	                method: 'create',
		    	                args: [{
		    	                	'name': item.name,
		    	                	'content': data,
		    	                	'directory': parent,
		    	                }],
		    	                context: _.extend({}, {
		    	                	mail_create_nosubscribe: true,
		    	                	mail_create_nolog: true,
									mail_notrack: true,
									tracking_disable: true
		    	                }, session.user_context),
						    }).then(function (id) {
						        progress--;
						        var status = parseInt((steps - progress).toFixed(0));
						        var percentage = parseInt((status / steps * 100).toFixed(0));
						        $notify.update({
						            message: message({ progress: status, total: steps }),
						            progress: percentage
						        });
						        if (status === steps) {
						            $finished.resolve(id);
						        }
						    }).fail(function () {
						        self.do_warn(item.name + _t(" couldn't be created!"));
						    });
						});
					} else if(item.isDirectory) {
						self._rpc({
			                model: 'muk_dms.directory',
			                method: 'create',
			                args: [{
			                	'name': item.name,
			                	'parent_directory': parent,
			                }],
			                context: _.extend({}, {
	    	                	mail_create_nosubscribe: true,
			                	mail_create_nolog: true,
								mail_notrack: true,
								tracking_disable: true
			                }, session.user_context),
						}).done(function(id) {
							for (var i = 0; i < item.files.length; i++) {
			    				create(item.files[i], id);
			    			}
			    		}).fail(function() {
			    			self.do_warn(item.name + _t(" couldn't be created!"));
			    		});
					}
				}
    			for (var i = 0; i < structure.length; i++) {
    				create(structure[i], node.data.odoo_id);
    			}
    			$.when($finished).then(function(id) {
    				$notify.close();
    				self.refreshNode(node);
                });
    		});
    	}
    },
    _moveNode: function(ev) {
    	var self = this;
		var vals = {};
    	var node = ev.data.node;
		var parent = this.renderer.$tree.jstree(true).get_node(ev.data.new_parent);
		if(node.data.odoo_model === "muk_dms.file") {
			vals.directory = parent.data.odoo_id;
		} else if(node.data.odoo_model === "muk_dms.directory") {
			vals.parent_directory = parent.data.odoo_id;
		}
		this._rpc({
            model: node.data.odoo_model,
            method: 'write',
            args: [node.data.odoo_id, vals],
            context: session.user_context,
		}).done(function() {
			self.do_notify(node.text + _t(" has been moved!"));
			self.refreshNode(ev.data.new_parent);
			self.refreshNode(ev.data.old_parent);
		}).fail(function() {
			self.do_warn(node.text + _t(" couldn't be moved!"));
			self.refreshNode(ev.data.new_parent);
			self.refreshNode(ev.data.old_parent);
		});
    },
    _deleteNode: function(ev) {
    	var self = this;
    	var node = ev.data.node;
    	var parent = this.renderer.$tree.jstree(true).get_parent(ev.data.node);
		this._rpc({
            model: node.data.odoo_model,
            method: 'unlink',
            args: [node.data.odoo_id],
            context: session.user_context,
		}).done(function() {
			self.do_notify(node.text + _t(" has been deleted!"));
			self.refreshNode(parent);
		}).fail(function() {
			self.refreshNode(parent);
			self.do_warn(node.text + _t(" couldn't be deleted!"));
		});
    },
    _copyNode: function(ev) {
    	var self = this;
		var vals = {};
    	var node = ev.data.node;
    	var original = ev.data.original;
		var parent = this.renderer.$tree.jstree(true).get_node(ev.data.parent);
		if(original.data.odoo_model === "muk_dms.file") {
			vals.directory = parent.data.odoo_id;
		} else if(original.data.odoo_model === "muk_dms.directory") {
			vals.parent_directory = parent.data.odoo_id;
		}
		this._rpc({
            model: original.data.odoo_model,
            method: 'copy',
            args: [original.data.odoo_id, vals],
            context: session.user_context,
		}).done(function(copy_id) {
			node.data = original.data;
			node.id = original.data.odoo_model.split(".") + "_" + copy_id;
			self.do_notify(node.text + _t(" has been copied!"));
			self.refreshNode(parent);
		}).fail(function() {
			self.refreshNode(parent);
			self.do_warn(node.text + _t(" couldn't be copied!"));
		});
    },
    _renameNode: function(ev) {
    	var self = this;
    	var node = ev.data.node;
		this._rpc({
            model: node.data.odoo_model,
            method: 'write',
            args: [node.data.odoo_id, {'name': ev.data.text}],
            context: session.user_context,
		}).done(function() {
			self.do_notify(node.text + _t(" has been renamed!"));
		}).fail(function() {
			self.refresh();
			self.do_warn(node.text + _t(" couldn't be renamed!"));
		});
    },
    _loadContextMenu: function(node, callback) {
    	var menu = {};
    	var jstree = this.renderer.$tree.jstree(true);
    	if(node.data) {
    		if(node.data.odoo_model === "muk_dms.directory") {
    			menu = this._loadContextMenuBasic(jstree, node, menu);
    			menu = this._loadContextMenuDirectory(jstree, node, menu);
    		} else if(node.data.odoo_model === "muk_dms.file") {
    			menu = this._loadContextMenuBasic(jstree, node, menu);
    			menu = this._loadContextMenuFile(jstree, node, menu);
    		}
    	}
    	return menu;
    },
    _loadContextMenuBasic: function($jstree, node, menu) {
    	var self = this;
    	menu.rename = {
			separator_before: false,
			separator_after: false,
			icon: "fa fa-pencil",
			label: _t("Rename"),
			action: function (data) {
				$jstree.edit(node);
			},
			_disabled: function (data) {
    			return !node.data.perm_write;
			},
		};
    	menu.action = {
			separator_before: false,
			separator_after: false,
			icon: "fa fa-bolt",
			label: _t("Actions"),
			action: false,
			submenu: {
				cut: {
					separator_before: false,
					separator_after: false,
					icon: "fa fa-scissors",
					label: _t("Cut"),
					action: function (data) {
						$jstree.cut(node);
					},
				},
				copy: {
					separator_before: false,
					separator_after: false,
					icon: "fa fa-clone",
					label: _t("Copy"),
					action: function (data) {
						$jstree.copy(node);
					},
				},
			},
			_disabled: function (data) {
				return !node.data.perm_read;
			},
		};
    	menu.delete = {
    		separator_before: false,
			separator_after: false,
			icon: "fa fa-trash-o",
			label: _t("Delete"),
			action: function (data) {
				$jstree.delete_node(node);
			},
			_disabled: function (data) {
    			return !node.data.perm_unlink;
			},
		};
    	return menu;
    },
    _loadContextMenuDirectory: function($jstree, node, menu) {
    	var self = this;
    	if(menu.action && menu.action.submenu) {
    		menu.action.submenu.paste = {
    			separator_before: false,
    			separator_after: false,
				icon: "fa fa-clipboard",
    			label: _t("Paste"),
    			action: function (data) {
    				$jstree.paste(node);
    			},
    			_disabled: function (data) {
	    			return !$jstree.can_paste() && !node.data.perm_create;
    			},
    		};
    	}
    	return menu;
    },
    _loadContextMenuFile: function($jstree, node, menu) {
    	var self = this;
    	menu.download = {
			separator_before: false,
			separator_after: false,
			icon: "fa fa-download",
			label: _t("Download"),
			action: function(data) {
				framework.blockUI();
				session.get_file({
				    'url': '/web/content',
				    'data': {
				        'id': node.data.odoo_id,
				        'download': true,
				        'field': 'content',
				        'model': 'muk_dms.file',
				        'filename_field': 'name',
				        'filename': node.data.filename
				    },
				    'complete': framework.unblockUI,
				    'error': crash_manager.rpc_error.bind(crash_manager)
				});
			}
    	};
    	return menu;
    },
});

return DocumentsController;

});