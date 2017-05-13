odoo.define('muk_dms.tree_view', function(require) {
	var core = require('web.core');
	var session = require('web.session');
	var framework = require('web.framework');
	var form_common = require('web.form_common');
	
	var Widget = require('web.Widget');
	var Dialog = require('web.Dialog');
	var Model = require("web.Model");

	var Preview = require('muk_dms.preview');
	
	var _t = core._t;
	var QWeb = core.qweb;

	var Directories = new Model('muk_dms.directory', session.user_context);
	var Files = new Model('muk_dms.file', session.user_context);
	
	var open = function(self, model, id) {
		self.do_action({
            type: 'ir.actions.act_window',
            res_model: model,
            res_id: id,
            views: [[false, 'form']],
            target: 'current',
            context: session.user_context,
        });
	}
	
	var edit = function(self, model, id) {
		self.do_action({
			type: 'ir.actions.act_window',
            res_model: model,
            res_id: id,
            views: [[false, 'form']],
            target: 'current',
            flags: {'initial_mode': 'edit'},
            context: session.user_context,
        });
	}

	var create = function(self, model, parent) {
		var context = {};
		if(model == "muk_dms.file") {
			context = $.extend(session.user_context, {
				default_directory: parent
            });
		} else if(model == "muk_dms.directory") {
			context = $.extend(session.user_context, {
				default_parent_id: parent
            });
		}
		self.do_action({
			type: 'ir.actions.act_window',
            res_model: model,
            views: [[false, 'form']],
            target: 'current',
            context: context,
        });
	}
	
	var context_menu_items = function(node, cp) {
		var items = {}
		if(node.data.perm_read) {
			items.open = {
				separator_before: false,
				separator_after: false,
				_disabled: false,
				icon: "fa fa-external-link-square",
				label: _t("Open"),
				action: function(data) {
					var inst = $.jstree.reference(data.reference);
					var	obj = inst.get_node(data.reference);
					open(inst.settings.widget, obj.data.odoo_model, obj.data.odoo_id);
				}
			};
		}
		if(node.data.perm_write) {
			items.edit = {
				separator_before: false,
				separator_after: false,
				_disabled: false,
				icon: "fa fa-pencil",
				label: _t("Edit"),
				action: function(data) {
					var inst = $.jstree.reference(data.reference);
					var	obj = inst.get_node(data.reference);
					edit(inst.settings.widget, obj.data.odoo_model, obj.data.odoo_id);
				}
			};
		}
		if(node.data.odoo_model == "muk_dms.file" && node.data.perm_read) {
			items.download = {
				separator_before: false,
				separator_after: false,
				_disabled: false,
				icon: "fa fa-download",
				label: _t("Download"),
				action: function(data) {
					var inst = $.jstree.reference(data.reference);
					var	obj = inst.get_node(data.reference);
					$.ajax({
		        	    url: obj.data.download_link,
		        	    type: "GET",
		        	    dataType: "binary",
		        	    processData: false,
		        	    beforeSend: function(xhr, settings) {
		        	    	framework.blockUI();
		        	    },
		        	    success: function(data, status, xhr){
		        		  	saveAs(data, obj.data.filename);
		        	    },
		        	    error:function(xhr, status, text) {
		        	    	self.do_warn(_t("Download..."), _t("An error occurred during download!"));
			  			},
		        	    complete: function(xhr, status) {
		        	    	framework.unblockUI();
		        	    },
		        	});
				}
			};
		} else if(node.data.odoo_model == "muk_dms.directory" && node.data.perm_create) {
			items.create = {
				separator_before: false,
				icon: "fa fa-plus-circle",
				separator_after: false,
				label: _t("Create"),
				action: false,
				submenu: {
					directory: {
						separator_before: false,
						separator_after: false,
						label: _t("Directory"),
						icon: "fa fa-folder",
						action: function(data) {
							var inst = $.jstree.reference(data.reference);
							var	obj = inst.get_node(data.reference);
							create(inst.settings.widget, "muk_dms.directory", obj.data.odoo_id);
						}
					},
					file : {
						separator_before: false,
						separator_after: false,
						label: _t("File"),
						icon: "fa fa-file",
						action: function(data) {
							var inst = $.jstree.reference(data.reference);
							var	obj = inst.get_node(data.reference);
							create(inst.settings.widget, "muk_dms.file", obj.data.odoo_id);
						}
					},
				}
			};
		}
		return items;
	}

	var DMSTreeViewWidget = Widget.extend({
		template: 'DMSTreeView',
		events: {
	        "click button.refresh": "refresh",
	        "click button.show_preview": "show_preview",
	        "click button.hide_preview": "hide_preview",
	        "click button.open": "open",
	        "click button.edit": "edit",
	        "click button.create_file": "create_file",
	        "click button.create_directory": "create_directory",
	    },
		init: function(parent) {
            this._super(parent);
            this.name = 'Document Tree';
    		this.splitter = false;
        },
        start: function () {
        	this.$('[data-toggle="tooltip"]').tooltip();
            this.load_view();
        },
        refresh: function() {
        	var self = this;
        	$.when(self.load_directories(self)).done(function (directories, directory_ids) {
        		$.when(self.load_files(self, directory_ids)).done(function (files) {
	        		var data = directories.concat(files);
	            	self.$el.find('.oe_document_tree').jstree(true).settings.core.data = data;
	            	self.$el.find('.oe_document_tree').jstree(true).refresh();
        		});
        	});
        },
        show_preview: function(ev) {
    		this.show_preview_active = true;
        	if(!this.$el.find('.show_preview').hasClass("active")) {
	        	this.$el.find('.show_preview').addClass("active");
	        	this.$el.find('.hide_preview').removeClass("active");
        		this.$el.find('.oe_document_col_preview').show();
	        	this.splitter = this.$el.find('.oe_document_row').split({
	        	    orientation: 'vertical',
	        	    limit: 100,
	        	    position: '60%'
	        	});
        	}
        },
        hide_preview: function(ev) {
    		this.show_preview_active = false;
        	if(!this.$el.find('.hide_preview').hasClass("active")) {
        		this.$el.find('.hide_preview').addClass("active");
        		this.$el.find('.show_preview').removeClass("active");
        		this.$el.find('.oe_document_col_preview').hide();
        		this.$el.find('.oe_document_col_tree').width('100%');
        		if(this.splitter) {
        			this.splitter.destroy();
        		}
        		this.splitter = false;
        	}
        },
        load_directories: function(self) {
        	var directories_query = $.Deferred();	
        	Directories.query(['name', 'parent_id', 'perm_read', 'perm_create',
        					   'perm_write', 'perm_unlink']).all().then(function(directories) {
        		var data = [];
        		var directory_ids = _.map(directories, function(directory, index) { 
        			return directory.id; 
        		});
        		_.each(directories, function(value, key, list) {
	        		data.push({
	        			id: "directory_" + value.id,
	        			parent: (value.parent_id && $.inArray(value.parent_id[0], directory_ids) !== -1 ? "directory_" + value.parent_id[0] : "#"),
	        			text: value.name,
	        			icon: "fa fa-folder-o",
	        			type: "directory",
	        			data: {
	        				container: false,
	        				odoo_id: value.id,
	        				odoo_parent_id: value.parent_id[0],
	        				odoo_model: "muk_dms.directory",
	        				perm_read: value.perm_read,
	        				perm_create: value.perm_create,
	        				perm_write: value.perm_write,
	        				perm_unlink: value.perm_unlink,
	        			}
	        		});
	        	});
        		directories_query.resolve(data, directory_ids);
        	});
        	return directories_query;
        },
        add_container_directory: function(self, directory_id, directory_name) {
        	return {
    			id: "directory_" + directory_id,
    			parent: "#",
    			text: directory_name,
    			icon: "fa fa-folder-o",
    			type: "directory",
    			data: {
    				container: true,
    				odoo_id: directory_id,
    				odoo_parent_id: false,
    				odoo_model: "muk_dms.directory",
    				perm_read: false,
    				perm_create: false,
    				perm_write: false,
    				perm_unlink: false,
    			}
        	};
        },
        load_files: function(self, directory_ids) {
        	var files_query = $.Deferred();
        	Files.query(['filename', 'mime_type', 'file_extension', 'directory',
        	             'link_preview', 'link_download', 'file_size', 'perm_read',
        	             'perm_create', 'perm_write', 'perm_unlink']).all().then(function(files) {
        		var data = [];
        		_.each(files, function(value, key, list) {
        			if(!($.inArray(value.directory[0], directory_ids) !== -1)) {
        				directory_ids.push(value.directory[0]);
        				data.push(self.add_container_directory(self, value.directory[0], value.directory[1]));
        			}
	        		data.push({
	        			id: "file," + value.id,
	        			parent: "directory_" + value.directory[0],
	        			text: value.filename,
	        			icon: mimetype2fa(value.mime_type, {prefix: "fa fa-"}),
	        			type: "file",
	        			data: {
		        			odoo_id: value.id,
	        				odoo_parent_id: value.directory[0],
		        			odoo_model: "muk_dms.file",
	        				filename: value.filename,
	        				file_size: value.file_size,
	        				preview_link: value.link_preview,
	        				download_link: value.link_download,
	        				file_extension: value.file_extension,
	        				mime_type: value.mime_type,
	        				perm_read: value.perm_read,
	        				perm_create: value.perm_create,
	        				perm_write: value.perm_write,
	        				perm_unlink: value.perm_unlink,
	        			}
	        		});
	        	});
        		files_query.resolve(data);
        	});
        	return files_query;
        },
        load_view: function() {
        	var self = this;
        	$.when(self.load_directories(self)).done(function (directories, directory_ids) {
        		$.when(self.load_files(self, directory_ids)).done(function (files) {
	        		var data = directories.concat(files);
	        		self.$el.find('.oe_document_tree').jstree({
	        			'widget': self,
			        	'core': {
			        		'animation': 0,
			        		'multiple': false,
			        	    'check_callback': true,
			        	    'themes': { "stripes": true },
			        		'data': data
			        	},
			        	'plugins': [
			        	    "contextmenu", "search", "sort", "state", "wholerow", "types"
	    	            ],
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
			        	'contextmenu': {
	    	                items: context_menu_items
	    	            },
		        	}).on('open_node.jstree', function (e, data) {
		        		data.instance.set_icon(data.node, "fa fa-folder-open-o"); 
		        	}).on('close_node.jstree', function (e, data) { 
		        		data.instance.set_icon(data.node, "fa fa-folder-o"); 
		        	}).bind('loaded.jstree', function(e, data) {
		        		self.show_preview();
		        	}).on('changed.jstree', function (e, data) {
		        		if(data.node) {
		        			self.selected_node = data.node;
		        			self.$el.find('button.open').prop('disabled', !self.selected_node.data.perm_read);
		        			self.$el.find('button.edit').prop('disabled', !self.selected_node.data.perm_write);
		        			self.$el.find('button.create_file').prop('disabled',
		        					self.selected_node.data.odoo_model != "muk_dms.directory" || !self.selected_node.data.perm_create);
		        			self.$el.find('button.create_directory').prop('disabled',
		        					self.selected_node.data.odoo_model != "muk_dms.directory" || !self.selected_node.data.perm_create);
		        			$("#menuContinenti").prop('disabled', function (_, val) { return ! val; });
		        			if(self.show_preview_active && data.node.data.odoo_model == "muk_dms.file") {
			        			$.when(Preview.PreviewHTML.getPreviewHTML(data.node.data.odoo_id, data.node.data.file_size,
			        					data.node.data.filename, data.node.data.file_extension, data.node.data.mime_type,
			        					data.node.data.preview_link)).done(function(result) {
				        				self.$el.find('.oe_document_preview').html(result);
				        		});	        		
			        		}
		        		}
		        	});
	        		var timeout = false;
	        		self.$el.find('#tree_search').keyup(function() {
		        	    if(timeout) {
		        	    	clearTimeout(timeout); 
		        	    }
		        	    timeout = setTimeout(function() {
		        	    	var v = self.$el.find('#tree_search').val();
		        	    	self.$('.oe_document_tree').jstree(true).search(v);
		        	    }, 250);
	        	   });
        		});
        	});
        },
        open: function() {
        	if(this.selected_node) {
        		open(this, this.selected_node.data.odoo_model, this.selected_node.data.odoo_id);
        	}
        },
        edit: function() {
        	if(this.selected_node) {
        		edit(this, this.selected_node.data.odoo_model, this.selected_node.data.odoo_id);
        	}
        },
        create_file: function() {
        	if(this.selected_node) {
        		if(this.selected_node.data.odoo_model == "muk_dms.directory") {
            		create(this, "muk_dms.file", this.selected_node.data.odoo_id);
        		} else {
            		create(this, "muk_dms.file", this.selected_node.data.odoo_id);
        		}
        	}
        },
        create_directory: function() {
        	if(this.selected_node) {
        		if(this.selected_node.data.odoo_model == "muk_dms.directory") {
            		create(this, "muk_dms.directory", this.selected_node.data.odoo_parent_id);
        		} else {
            		create(this, "muk_dms.file", this.selected_node.data.odoo_parent_id);
        		}
        	}
        },
	});

	core.action_registry.add('muk_dms.tree_view', DMSTreeViewWidget);

	return {
		DMSTreeViewWidget : DMSTreeViewWidget,
	};
});