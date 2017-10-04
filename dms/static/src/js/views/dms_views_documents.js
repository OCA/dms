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

odoo.define('muk_dms_views.documents', function(require) {
"use strict";

var ajax = require('web.ajax');
var core = require('web.core');
var config = require('web.config');
var session = require('web.session');
var web_client = require('web.web_client');
var framework = require('web.framework');
var crash_manager = require('web.crash_manager');

var dms_utils = require('muk_dms.utils');

var ControlPanelMixin = require('web.ControlPanelMixin');
var PreviewHelper = require('muk_dms_preview_file.PreviewHelper');

var Widget = require('web.Widget');
var Dialog = require('web.Dialog');

var _t = core._t;
var QWeb = core.qweb;

var DocumentTreeView = Widget.extend(ControlPanelMixin, {
	cssLibs: [
        '/muk_dms/static/lib/jquery-splitter/css/jquery.splitter.css',
        '/muk_dms/static/lib/jsTree/themes/proton/style.css',
    ],
    jsLibs: [
        '/muk_dms/static/lib/jquery-splitter/js/jquery.splitter.js',
        '/muk_dms/static/lib/jsTree/jstree.js',
    ],
	template: 'muk_dms.DocumentTreeView',
	events: _.extend({}, Widget.prototype.events, {
		'dragenter .oe_document_col_tree': '_dragenter_dropzone',
		'dragover .oe_document_col_tree': '_dragover_dropzone',
		'dragleave .oe_document_col_tree': '_dragleave_dropzone',
		'drop .oe_document_col_tree': '_drop_dropzone',
	}),
	init: function(parent, context) {
        this._super(parent, context);
        this.splitter = false;
        this.auto_refresh = true;
        this.action_open_dialog = false;
        this.FileReaderAPI = window.File && window.FileReader &&
        	window.FileList && window.Blob;
    },
    willStart: function() {
         return $.when(ajax.loadLibs(this), this._super());
    },
    start: function() {
        var self = this;
        return this._super().then(function() {
            self.update_cp();
            self.render();
        	self.$('[data-toggle="tooltip"]').tooltip();
            self.$el.parent().addClass('oe_background_grey');
            if(self.FileReaderAPI) {
            	var dropzone = self.$el.find('.oe_document_col_tree');
                dropzone.dndHover().on({
                    'dndHoverStart': function(ev) {
                    	if(self.FileReaderAPI) {
	                    	dropzone.addClass('oe_document_dropzone');
	                    	ev.stopPropagation();
	                    	ev.preventDefault();
	                        return false;
                    	}
                    },
                    'dndHoverEnd': function(ev) {
                    	dropzone.removeClass('oe_document_dropzone');
                    	ev.stopPropagation();
                    	ev.preventDefault();
                        return false;
                    }
                });
        	}
        });
    },
    toggle_dialog: function() {
    	this.action_open_dialog = !this.action_open_dialog;
    	this.$pager.find('.action_dialog').toggleClass("active");
    },
    refresh: function(skip_loading, timeout) {
    	var self = this;
    	if(this.$tree && this.auto_refresh) {
    		dms_utils.delay(function() {
    			self.$tree.jstree(true).refresh(skip_loading || false);
		    }, timeout || 0);
    	}
    },
    refresh_node: function(obj, timeout) {
    	var self = this;
    	if(this.$tree && this.auto_refresh) {
    		if(obj && obj.data && obj.data.odoo_model !== 'muk_dms.settings') {
    			dms_utils.delay(function() {
    				self.$tree.jstree(true).refresh_node(obj);
    		    }, timeout || 0);
    		} else {
    			self.refresh();
    		}
    	}
    },
    toggle_refresh: function() {
    	this.auto_refresh = !this.auto_refresh;
    	this.$pager.find('.auto_refresh').toggleClass("active");
    	this.$pager.find('.refresh').prop("disabled", !this.auto_refresh);
    },
    on_reverse_breadcrumb: function() {
        web_client.do_push_state({});
        this.update_cp();
        this.refresh(true, 0, true);
    },
    render: function() {
        var self = this;
        this.$tree = this.$el.find('.oe_document_tree').jstree({
        	'core' : {
        		'animation': 0,
        		'widget': self,
        		'multiple': true,
        	    'check_callback': self._check_callback,
        		'themes': {
                    'name': 'proton',
                    'responsive': true
                },
        		'data': function (node, callback) {
        			if(node.id === "#") {
        				self._load_data().then(function(settings) {
        					callback.call(this, _.map(settings, function (setting) {
        						var child_directories = _.map(setting.top_directories, function (directory) {
        							return self._node_directory(directory);
        						});
        						var child_files =_.map(setting.top_files, function (file) {
        							return self._node_file(file);
        						});
        						return {
        							id: "setting_" + setting.id,
        							text: setting.name,
        							icon: "fa fa-database",
        	  	        			type: "settings",
        	  	        			data: {
        		        				odoo_id: setting.id,
        		        				odoo_model: "muk_dms.settings",
        		        			},
        		        			children: child_directories.concat(child_files),
        		                  };
        					}));
        				});
        	    	} else {
        	    		self._load_node(node).then(function(node) {
        	    			callback.call(this, node);
        	    		});
        	    	}
        		},
        	},
        	'contextmenu': {
                items: self._load_contextmenu
            },
            'search': {
         	    'case_insensitive': false,
         	    'show_only_matches': true,
         	    'search_callback': function (str, node) {
         	    	try {
         	    		return node.text.match(new RegExp(str)); 
         	    	} catch(ex) {
         	    		return false; 
         	    	} 
         	    }
         	},
        	'state' : {
        		'key' : "documents" 
        	},
	        'plugins': [
	        	"dnd", "wholerow", "types", "state", "sort", "contextmenu", "search",
	        ],
    	}).on('open_node.jstree', function (e, data) {
    		if(data.node.data && data.node.data.odoo_model === "muk_dms.directory") {
    			data.instance.set_icon(data.node, "fa fa-folder-open-o"); 
    		}
    	}).on('close_node.jstree', function (e, data) { 
    		if(data.node.data && data.node.data.odoo_model === "muk_dms.directory") {
        		data.instance.set_icon(data.node, "fa fa-folder-o"); 
    		}
    	}).on('loaded.jstree', function(e, data) {
    		if(!config.device.isMobile) {
    			self.show_preview();
    		}
    	}).on('changed.jstree', function (e, data) {
    		self._update_jstree(data);
    	}).on('move_node.jstree', function(e, data) {
    		self._move_node(data.node, data.parent);
    	}).on('copy_node.jstree', function(e, data) {
    		self._copy_node(data.node, data.original, data.parent);
    	}).on('rename_node.jstree', function(e, data) {
    		self._rename_node(data.node, data.text, data.old);
    	}).on('delete_node.jstree', function(e, data) {
    		self._delete_node(data.node, data.parent);
    	});
 		self.$searchview.find('#tree_search').keyup(function() {
 			dms_utils.delay(function() {
 				var v = self.$searchview.find('#tree_search').val();
     	    	self.$tree.jstree(true).search(v);
		    }, 200);
 	   });
    },
    update_cp: function() {
    	if (!this.$buttons) {
            this.$buttons = $(QWeb.render('muk_dms.DocumentTreeViewButtons', {
                widget: this,
            }));
            this.$buttons.find('.open').on('click', _.bind(this._open_node, this));
            this.$buttons.find('.edit').on('click', _.bind(this._edit_node, this));
        }
    	if (!this.$pager) {
            this.$pager = $(QWeb.render('muk_dms.DocumentTreeViewActions', {
                widget: this,
            }));
            this.$pager.find('.refresh').on('click', _.bind(this.refresh, this));
            this.$pager.find('.auto_refresh').on('click', _.bind(this.toggle_refresh, this));
            this.$pager.find('.action_dialog').on('click', _.bind(this.toggle_dialog, this));
        }
    	if (!this.$switch_buttons) {
            this.$switch_buttons = $(QWeb.render('muk_dms.DocumentTreeViewOptions', {
                widget: this,
            }));
        }
    	if (!this.$searchview) {
            this.$searchview = $(QWeb.render('muk_dms.DocumentTreeViewSearch', {
                widget: this,
            }));
        }
        this.update_control_panel({
            cp_content: {
                $buttons: this.$buttons,
                $pager: this.$pager,
                $searchview: this.$searchview,
                $switch_buttons: this.$switch_buttons,
            },
            breadcrumbs: this.getParent().get_breadcrumbs(),
        });
        this.$switch_buttons.parent().find('.show_preview').on('click', _.bind(this.show_preview, this));
        this.$switch_buttons.parent().find('.hide_preview').on('click', _.bind(this.hide_preview, this));
    },
    show_preview: function() {
		this.show_preview_active = true;
    	if(!this.$switch_buttons.parent().find('.show_preview').hasClass("active")) {
        	this.$switch_buttons.parent().find('.show_preview').addClass("active");
        	this.$switch_buttons.parent().find('.hide_preview').removeClass("active");
    		this.$el.find('.oe_document_col_preview').show();
        	this.splitter = this.$el.find('.oe_document_row').split({
        	    orientation: 'vertical',
        	    limit: 100,
        	    position: '60%'
        	});
    	}
    },
    hide_preview: function() {
		this.show_preview_active = false;
    	if(!this.$switch_buttons.parent().find('.hide_preview').hasClass("active")) {
    		this.$switch_buttons.parent().find('.hide_preview').addClass("active");
    		this.$switch_buttons.parent().find('.show_preview').removeClass("active");
    		this.$el.find('.oe_document_col_preview').hide();
    		this.$el.find('.oe_document_col_tree').width('100%');
    		if(this.splitter) {
    			this.splitter.destroy();
    		}
    		this.splitter = false;
    	}
    },
    _load_data: function() {
    	var self = this;
    	var data_loaded = $.Deferred();
    	var data_parts = [];
    	this._rpc({
            fields: ['name', 'top_directories', 'top_files'],
            domain: [['show_tree', '=', true]],
            model: 'muk_dms.settings',
            method: 'search_read',
            context: session.user_context,
        }).then(function(settings) {
        	_.each(settings, function(setting, index, settings) {
        		if(setting.top_directories.length > 0) {
        			var data_part_directory = $.Deferred();
        			data_parts.push(data_part_directory);
	        		self._rpc({
	                    fields: [
	                    	'name', 'parent_directory', 
	                    	'size', 'perm_read', 'perm_create',
	      				  	'perm_write', 'perm_unlink',
	      				  	'count_directories', 'count_files',
	      				],
	                    domain: [
	                    	['id', 'in', setting.top_directories]
	                    ],
	                    model: 'muk_dms.directory',
	                    method: 'search_read',
	                    context: session.user_context,
	                }).then(function(directories) {
	                	settings[index].top_directories = directories;
	                	data_part_directory.resolve(directories);
	                });
        		}
        		if(setting.top_files.length > 0) {
        			var data_part_file = $.Deferred();
        			data_parts.push(data_part_file);
	        		self._rpc({
	                    fields: [
	                    	'name', 'mimetype', 'extension', 
	      				  	'directory', 'size', 'perm_read',
	      				  	'perm_create', 'perm_write', 
	      				  	'perm_unlink', 'locked',
	      				],
	                    domain: [
	                    	['id', 'in', setting.top_files]
	                    ],
	                    model: 'muk_dms.file',
	                    method: 'search_read',
	                    context: session.user_context,
	                }).then(function(files) {
	                	settings[index].top_files = files;
	                	data_part_file.resolve(files);
	                });
        		}
        	});
        	$.when.apply($, data_parts).then(function() {
            	data_loaded.resolve(settings);
        	});
        });
        return data_loaded;
    },
    _load_node(node) {
    	var self = this;
    	var result = $.Deferred();
    	if(node.data && node.data.odoo_model === "muk_dms.directory") {
    		var directories_loaded = $.Deferred();
    		var files_loaded = $.Deferred();
    		this._rpc({
                fields: [
                	'name', 'parent_directory', 
                	'size', 'perm_read', 'perm_create',
  				  	'perm_write', 'perm_unlink',
  				  	'count_directories', 'count_files',
  				],
                domain: [
                	['parent_directory', '=', node.data.odoo_id]
                ],
                model: 'muk_dms.directory',
                method: 'search_read',
                context: session.user_context,
            }).then(function(directories) {
            	directories_loaded.resolve(_.map(directories, function (directory) {
					return self._node_directory(directory);
				}));
            });
    		this._rpc({
                fields: [
                	'name', 'mimetype', 'extension', 
  				  	'directory', 'size', 'perm_read',
  				  	'perm_create', 'perm_write', 
  				  	'perm_unlink', 'locked',
  				],
                domain: [
                	['directory', '=', node.data.odoo_id]
                ],
                model: 'muk_dms.file',
                method: 'search_read',
                context: session.user_context,
            }).then(function(files) {
            	files_loaded.resolve(_.map(files, function (file) {
					return self._node_file(file);
				}));
            });
    		$.when(directories_loaded, files_loaded).then(function(directories, files) {
    			result.resolve(directories.concat(files));
    		});
    	} else {
    		result.resolve([]);
    	}
    	return result;
    },
    _node_directory(directory) {
    	return {
			id: "directory_" + directory.id,
			text: directory.name,
			icon: "fa fa-folder-o",
			type: "directory",
			data: {
				odoo_id: directory.id,
				odoo_model: "muk_dms.directory",
				name: directory.name,
				size: dms_utils.format_size(directory.size),
				perm_read: directory.perm_read,
				perm_create: directory.perm_create,
				perm_write: directory.perm_write,
				perm_unlink: directory.perm_unlink,
				directories: directory.count_directories,
				files: directory.count_files,
			},
			children: (directory.count_directories +
					directory.count_files) > 0 ? true : false,
		}
    },
    _node_file(file) {
    	return {
			id: "file_" + file.id,
			text: file.name,
			icon: dms_utils.mimetype2fa(file.mimetype, {prefix: "fa fa-"}),
			type: "file",
			data: {
				odoo_id: file.id,
				odoo_model: "muk_dms.file",
				name: file.name,
				size: dms_utils.format_size(file.size),
				mimetype: file.mimetype,
				extension: file.extension,
				locked: file.locked,
				perm_read: file.perm_read,
				perm_create: file.perm_create,
				perm_write: file.perm_write,
				perm_unlink: file.perm_unlink,
			},
		}
    },
    _check_callback: function (operation, node, parent, position, more) {
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
    			var self = this;
    			var names = [];
    			_.each(parent.children, function(child, index, children) {
    				var child_node = self.get_node(child);
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
    _preview_node: function(node) {
    	var self = this;
    	if(node.data && node.data.odoo_model === "muk_dms.file") {
    		PreviewHelper.createFilePreviewContent(node.data.odoo_id, self).then(function($content) {
    			self.$el.find('.oe_document_preview').html($content);
    		});
    	} else if(node.data && node.data.odoo_model === "muk_dms.directory") {
    		self.$el.find('.oe_document_preview').html(
    				$(QWeb.render('muk_dms.DocumentTreeViewDirectoryPreview', {
			            widget: this,
			            directory: node.data,
    				})));
    	}
    },
    _update_jstree: function(data) {
    	if(data.action === "select_node" && data.node) {
			if(data.selected.length === 1) {
    			if(this.show_preview_active) {
    				this._preview_node(data.node);
    			}
    			this.$buttons.find('button.open').prop('disabled', !data.node.data.perm_read);
    			this.$buttons.find('button.edit').prop('disabled', !data.node.data.perm_write);
			} else {
				this.$buttons.find('button.open').prop('disabled', true);
				this.$buttons.find('button.edit').prop('disabled', true);
			}
		}
    	$("#menuContinenti").prop('disabled', function (_, val) { return ! val; });
    },
    _open_node: function() {
    	if(this.$tree) {
    		var selected = this.$tree.jstree(true).get_selected();
    		var node = selected.length > 0 ? 
    				this.$tree.jstree(true).get_node(selected[0]) : {};
    		if(node.data) {
    			this.do_action({
    	    		type: 'ir.actions.act_window',
    	            res_model: node.data.odoo_model,
    	            res_id: node.data.odoo_id,
    	            views: [[false, 'form']],
    	            target: this.action_open_dialog ? 'new' : 'current',
    	            flags: {'form': {'initial_mode': 'readonly'}},
    	            context: session.user_context,
    	        }, {
    	            on_reverse_breadcrumb: this.on_reverse_breadcrumb
    	        });
    		}
    	}
    },
    _edit_node: function() {
    	if(this.$tree) {
    		var selected = this.$tree.jstree(true).get_selected();
    		var node = selected.length > 0 ? 
    				this.$tree.jstree(true).get_node(selected[0]) : {};
    		if(node.data) {
    			this.do_action({
    	    		type: 'ir.actions.act_window',
    	            res_model: node.data.odoo_model,
    	            res_id: node.data.odoo_id,
    	            views: [[false, 'form']],
    	            target: this.action_open_dialog ? 'new' : 'current',
    	    	    flags: {'form': {'mode': 'edit', 'initial_mode': 'edit'}},
    	            context: session.user_context,
    	        }, {
    	            on_reverse_breadcrumb: this.on_reverse_breadcrumb
    	        });
    		}
    	}
    },
    _move_node: function(node, parent) {
    	var self = this;
    	if(this.$tree) {
    		var parent = this.$tree.jstree(true).get_node(parent);
    		var vals = {};
    		if(node.data && parent.data && 
    				node.data.odoo_model === "muk_dms.file") {
    			vals.directory = parent.data.odoo_id;
    		} else if(node.data && parent.data && 
    				node.data.odoo_model === "muk_dms.directory") {
    			vals.parent_directory = parent.data.odoo_id;
    		}
    		this._rpc({
                model: node.data.odoo_model,
                method: 'write',
                args: [node.data.odoo_id, vals],
                context: session.user_context,
    		}).done(function() {
    			self.do_notify(node.text + _t(" has been moved!"));
    			self.refresh();
    		}).fail(function() {
    			self.refresh();
    			self.do_warn(node.text + _t(" couldn't be moved!"));
    		});
    	}
    },
    _delete_node: function(node, parent) {
    	var self = this;
    	if(this.$tree && node.data) {
    		this._rpc({
                model: node.data.odoo_model,
                method: 'unlink',
                args: [node.data.odoo_id],
                context: session.user_context,
    		}).done(function() {
    			self.do_notify(node.text + _t(" has been deleted!"));
    			self.refresh();
    		}).fail(function() {
    			self.refresh();
    			self.do_warn(node.text + _t(" couldn't be deleted!"));
    		});
    	}
    },
    _copy_node: function(node, original, parent) {
    	var self = this;
    	if(this.$tree) {
    		var parent = this.$tree.jstree(true).get_node(parent);
    		var vals = {};
    		if(original.data && parent.data && 
    				original.data.odoo_model === "muk_dms.file") {
    			vals.directory = parent.data.odoo_id;
    		} else if(original.data && parent.data && 
    				original.data.odoo_model === "muk_dms.directory") {
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
    			self.refresh();
    		}).fail(function() {
    			self.refresh();
    			self.do_warn(node.text + _t(" couldn't be copied!"));
    		});
    	}
    },
    _rename_node: function(node, new_name, old_name) {
    	var self = this;
    	if(this.$tree && node.data) {
    		this._rpc({
                model: node.data.odoo_model,
                method: 'write',
                args: [node.data.odoo_id, {'name': new_name}],
                context: session.user_context,
    		}).done(function() {
    			self.do_notify(node.text + _t(" has been renamed!"));
    		}).fail(function() {
    			self.refresh();
    			self.do_warn(node.text + _t(" couldn't be renamed!"));
    		});
    	}
    },
    _create_node: function(node, type) {
    	var context = {};
    	if(this.$tree && node.data) {
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
	            target: 'current',
	            context: context,
	        }, {
	            on_reverse_breadcrumb: this.on_reverse_breadcrumb
	        });
    	}
    },
    _load_contextmenu: function(node, callback) {
    	var menu = {};
    	var widget = this.settings.core.widget;
    	if(node.data) {
    		menu = widget._load_contextmenu_basic(this, node, menu);
    		if(node.data.odoo_model === "muk_dms.directory") {
    			menu = widget._load_contextmenu_directory(this, node, menu);
    		} else if(node.data.odoo_model === "muk_dms.file") {
    			menu = widget._load_contextmenu_file(this, node, menu);
    		}
    	}
    	return menu;
    },
    _load_contextmenu_basic: function($jstree, node, menu) {
    	var self = this;
    	menu.open = {
			separator_before: false,
			separator_after: false,
			icon: "fa fa-external-link",
			label: _t("Open"),
			action: function (data) {
				self._open_node();
			},
		},
		menu.edit = {
			separator_before: false,
			separator_after: false,
			icon: "fa fa-pencil-square-o",
			label: _t("Edit"),
			action: function (data) {
				self._edit_node();
			},
			_disabled: function (data) {
    			return !node.data.perm_write;
			},
		},
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
		},
		menu.delete = {
    		separator_before: false,
			separator_after: false,
			icon: "fa fa-trash-o",
			label: _t("Delete"),
			action: function (data) {
				if($jstree.is_selected(node)) {
					$jstree.delete_node($jstree.get_top_selected());
				} else {
					$jstree.delete_node(node);
				}
			},
			_disabled: function (data) {
    			return !node.data.perm_unlink;
			},
		},
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
						if($jstree.is_selected(node)) {
							$jstree.cut($jstree.get_top_selected());
						} else {
							$jstree.cut(node);
						}
					}
				},
				copy: {
					separator_before: false,
					separator_after: false,
					icon: "fa fa-clone",
					label: _t("Copy"),
					action: function (data) {
						if($jstree.is_selected(node)) {
							$jstree.copy($jstree.get_top_selected());
						} else {
							$jstree.copy(node);
						}
					}
				},
			}
		}
    	return menu;
    },
    _load_contextmenu_directory: function($jstree, node, menu) {
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
    		}
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
    						self._create_node(node, "muk_dms.directory");
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
    						self._create_node(node, "muk_dms.file");
    					},
    					_disabled: function (data) {
    		    			return !node.data.perm_create;
    	    			},
    				},
    			}	
    		}
    	}
    	return menu;
    },
    _load_contextmenu_file: function($jstree, node, menu) {
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
    	}
    	return menu;
    },
    _dragenter_dropzone: function(ev) {
    	if(this.FileReaderAPI) {
	    	ev.preventDefault();
    	}
    },
    _dragover_dropzone: function(ev) {
    	if(this.FileReaderAPI && ev.originalEvent.dataTransfer) {
        	ev.preventDefault();
    		ev.originalEvent.dataTransfer.dropEffect = 'copy';
    	}
    },
    _dragleave_dropzone: function(ev) {
    	if(this.FileReaderAPI) {
	    	ev.preventDefault();
    	}
    },
    _drop_dropzone: function(ev) {
    	var self = this;
    	function traverse_items(item, parent) {
    		var $event = $.Deferred();
		    if(item.isFile) {
		    	item.file(function(file) {
			    	var fileReader = new FileReader();
			    	fileReader.readAsDataURL(file);
			    	fileReader.onloadend = function (upload) {
			    		var data = upload.target.result;
	                    data = data.split(',')[1];
	                    self._rpc({
	    	                model: 'muk_dms.file',
	    	                method: 'create',
	    	                args: [{
	    	                	'name': file.name,
	    	                	'content': data,
	    	                	'directory': parent,
	    	                }],
	    	                context: session.user_context,
	    	    		}).done(function() {
	    	    			$event.resolve();
	    	    			self.do_notify(file.name + _t(" has been created!"));
	    	    		}).fail(function() {
	    	    			self.do_warn(file.name + _t(" couldn't be created!"));
	    	    		});
	                };
			    });
		    } else if(item.isDirectory) {
			    var dirReader = item.createReader();
			    self._rpc({
	                model: 'muk_dms.directory',
	                method: 'create',
	                args: [{
	                	'name': item.name,
	                	'parent_directory': parent,
	                }],
	                context: session.user_context,
	    		}).done(function(id) {
	    			dirReader.readEntries(function(entries) {
				    	var events = [];
	    				for (var i = 0; i < entries.length; i++) {
	    					events.push(traverse_items(entries[i], id));
				        }
	    				$.when.apply($, events).then(function() {
	    					$event.resolve();
	    	        	});
				    });
	    		}).fail(function() {
	    			self.do_warn(item.name + _t(" couldn't be created!"));
	    		});
		    }
            return $event;
		}
    	if(this.$tree && ev.originalEvent.dataTransfer) {
    		var selected = this.$tree.jstree(true).get_selected();
    		var node = selected.length > 0 ? 
    				this.$tree.jstree(true).get_node(selected[0]) : false;
    		if(node && node.data && node.data.odoo_model === "muk_dms.file") {
    			node = this.$tree.jstree(true).get_node(node.parent) || false;
    		}
    		if(node && node.data && node.data.odoo_model !== 'muk_dms.settings') {
	    		ev.stopPropagation();
	            ev.preventDefault();
	            var items = ev.originalEvent.dataTransfer.items;
	            for (var i = 0; i < items.length; i++) {
		        	var item = items[i].webkitGetAsEntry();
		        	if (item) {
		        		traverse_items(item, node.data.odoo_id).then(function() {
		        			var parent = self.$tree.jstree(true).get_node(node.parent) || false
		        			self.refresh_node(parent);
		            	});
		            } else {
		            	self.do_warn(_t("Your browser doesn't support Drag and Drop!"));
		            }
		        }
    		} else {
    			self.do_warn(_t("No directory has been selected!"));
    		}
    	}
    },
});

core.action_registry.add('muk_dms_views.documents', DocumentTreeView);

return DocumentTreeView

});