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

odoo.define('muk_dms_views.DocumentsModel', function(require) {
"use strict";

var ajax = require('web.ajax');
var core = require('web.core');
var mixins = require('web.mixins');
var config = require('web.config');
var session = require('web.session');
var fieldUtils = require('web.field_utils');

var utils = require('muk_web_utils.common');
var mimetype = require('muk_web_utils.mimetype');

var Class = require('web.Class');
var Domain = require('web.Domain');
var ServicesMixin = require('web.ServicesMixin');

var _t = core._t;
var QWeb = core.qweb;

var DocumentsModel = Class.extend(mixins.EventDispatcherMixin, ServicesMixin, {
	init: function (parent, params) {
        mixins.EventDispatcherMixin.init.call(this);
        this.params = params || {};
        this.setParent(parent);
    },
    setParams: function(params) {
        this.params = params || {};
    },
    load: function(node, params) {
    	var args = _.extend({}, {
    		settings: {},
    		directory: {},
    		file: {},
    		search: {},
    	}, this.params, params || {});
    	if((!node || node.id === "#") && args.init_data) {
    		return args.init_data;
    	} else if(!node || node.id === "#") {
    		return this._loadInitialData(args);
    	} else {
    		return this._loadNode(node, args);
    	}
    },
    massload: function(nodes, params) {
    	var args = _.extend({}, {
    		settings: {},
    		directory: {},
    		file: {},
    		search: {},
    	}, this.params, params || {});
    	return this._loadNodes(nodes, args);
    },
    search: function(val, node, params) {
    	var args = _.extend({}, {
    		settings: {},
    		directory: {},
    		file: {},
    		search: {},
    	}, this.params, params || {});
    	return this._searchNodes(val, node, args);
    },
    _buildDomain: function(base, domain) {
    	var result = new Domain(base);
    	result._addSubdomain(domain || []);
    	return result.toArray();
    },
    _loadInitialData: function(args) {
    	var self = this;
    	var data_parts = [];
    	var data_loaded = $.Deferred();
    	this._rpc({
            fields: _.union(args.settings.fields || [], ['name', 'top_directories', 'top_files']),
            domain: args.settings.domain || [['show_tree', '=', true]],
            model: 'muk_dms.settings',
            method: 'search_read',
            context: args.settings.context || session.user_context,
        }).then(function(settings) {
        	_.each(settings, function(setting, index, settings) {
        		if(setting.top_directories.length > 0) {
        			var data_part_directory = $.Deferred();
        			data_parts.push(data_part_directory);
	        		self._rpc({
	                    fields: _.union(args.directory.fields || [], [
	                    	'name', 'parent_directory', 'locked',
	                    	'permission_read', 'permission_create',
	      				  	'permission_write', 'permission_unlink',
	      				  	'count_directories', 'count_files',
	      				]),
	                    domain: self._buildDomain([['id', 'in', setting.top_directories]], args.directory.domain), 
	                    model: 'muk_dms.directory',
	                    method: 'search_read',
	                    context: args.directory.context || session.user_context,
	                }).then(function(directories) {
	                	settings[index].top_directories = directories;
	                	data_part_directory.resolve(directories);
	                });
        		}
        		if(setting.top_files.length > 0 && !args.directoriesOnly) {
        			var data_part_file = $.Deferred();
        			data_parts.push(data_part_file);
	        		self._rpc({
	                    fields: _.union(args.file.fields || [], [
	                    	'name', 'mimetype', 'extension', 
	      				  	'directory', 'size', 'permission_read',
	      				  	'permission_create', 'permission_write', 
	      				  	'permission_unlink', 'locked',
	      				]),
	                    domain: self._buildDomain([['id', 'in', setting.top_files]], args.file.domain),
	                    model: 'muk_dms.file',
	                    method: 'search_read',
	                    context: args.file.context || session.user_context,
	                }).then(function(files) {
	                	settings[index].top_files = files;
	                	data_part_file.resolve(files);
	                });
        		}
        	});
        	$.when.apply($, data_parts).then(function() {
        		if(!args.noSettings) {
        			data_loaded.resolve(_.chain(settings).map(function (setting) {
						var child_directories = _.map(setting.top_directories, function (directory) {
							return self._makeNodeDirectory(directory, args.directoriesOnly);
						});
						var child_files =_.map(setting.top_files, function (file) {
							return self._makeNodeFile(file);
						});
						return {
							id: "setting_" + setting.id,
							text: setting.name,
							icon: "fa fa-database",
	  	        			type: "settings",
	  	        			data: {
		        				odoo_id: setting.id,
		        				odoo_model: "muk_dms.settings",
		        				odoo_record: setting,
		        			},
		        			children: child_directories.concat(child_files),
		                  };
					}).filter(function(node) {
						return node.children && node.children.length > 0;
					}).value());
        		} else {
        			var nodes = [];
        			_.each(settings, function(setting, index, settings) {
        				_.each(setting.top_directories, function(directory, index, directories) {
        					nodes.push(self._makeNodeDirectory(directory, args.directoriesOnly));
            			});
        				_.each(setting.top_files, function(file, index, files) {
        					nodes.push(self._makeNodeFile(file));
            			});
        			});
        			data_loaded.resolve(nodes);
        		}
        	});
        });
        return data_loaded;
    },
    _loadNode: function(node, args) {
    	var self = this;
    	var result = $.Deferred();
    	if(node.data && node.data.odoo_model === "muk_dms.directory") {
    		var directories_loaded = $.Deferred();
    		var files_loaded = $.Deferred();
    		this._rpc({
                fields: _.union(args.directory.fields || [], [
                	'name', 'parent_directory', 'locked', 
                	'permission_read', 'permission_create',
  				  	'permission_write', 'permission_unlink',
  				  	'count_directories', 'count_files',
  				]),
                domain: this._buildDomain([['parent_directory', '=', node.data.odoo_id]], args.directory.domain), 
                model: 'muk_dms.directory',
                method: 'search_read',
                context: args.directory.context || session.user_context,
            }).then(function(directories) {
            	directories_loaded.resolve(_.map(directories, function (directory) {
					return self._makeNodeDirectory(directory, args.directoriesOnly);
				}));
            });
    		if(args.directoriesOnly) {
    			files_loaded.resolve([]);
    		} else {
	    		this._rpc({
	                fields: _.union(args.file.fields || [], [
	                	'name', 'mimetype', 'extension', 
	  				  	'directory', 'size', 'permission_read',
	  				  	'permission_create', 'permission_write', 
	  				  	'permission_unlink', 'locked',
	  				]),
	                domain: this._buildDomain([['directory', '=', node.data.odoo_id]], args.file.domain),
	                model: 'muk_dms.file',
	                method: 'search_read',
	                context: session.user_context,
	            }).then(function(files) {
	            	files_loaded.resolve(_.map(files, function (file) {
						return self._makeNodeFile(file);
					}));
	            });
    		}
    		$.when(directories_loaded, files_loaded).then(function(directories, files) {
    			result.resolve(directories.concat(files));
    		});
    	} else {
    		result.resolve([]);
    	}
    	return result;
    },
    _loadNodes: function(nodes, args) {
    	var self = this;
    	var result = $.Deferred();
    	var ids = _.chain(nodes).filter(function(node, i) {
    		var tuple = node.split("_");
     		return tuple[0] === "directory";
    	 }).map(function(node, i) { 
    		 var tuple = node.split("_");
    		 return parseInt(tuple[1]);
    	 }).value();
    	if(ids.length > 0) {
    		var directories_loaded = $.Deferred();
    		var files_loaded = $.Deferred();
    		this._rpc({
                fields: _.union(args.directory.fields || [], [
                	'name', 'parent_directory', 'locked', 
                	'permission_read', 'permission_create',
  				  	'permission_write', 'permission_unlink',
  				  	'count_directories', 'count_files',
  				]),
                domain: this._buildDomain([['parent_directory', 'in', ids]], args.directory.domain), 
                model: 'muk_dms.directory',
                method: 'search_read',
                context: args.directory.context || session.user_context,
            }).then(function(directories) {
            	directories_loaded.resolve(_.map(directories, function (directory) {
					return self._makeNodeDirectory(directory, args.directoriesOnly);
				}));
            });
    		if(args.directoriesOnly) {
    			files_loaded.resolve([]);
    		} else {
	    		this._rpc({
	                fields: _.union(args.file.fields || [], [
	                	'name', 'mimetype', 'extension', 
	  				  	'directory', 'size', 'permission_read',
	  				  	'permission_create', 'permission_write', 
	  				  	'permission_unlink', 'locked',
	  				]),
	                domain: this._buildDomain([['directory', 'in', ids]], args.file.domain),
	                model: 'muk_dms.file',
	                method: 'search_read',
	                context: session.user_context,
	            }).then(function(files) {
	            	files_loaded.resolve(_.map(files, function (file) {
						return self._makeNodeFile(file);
					}));
	            });
    		}
    		$.when(directories_loaded, files_loaded).then(function(directories, files) {
    			var tree = _.groupBy(_.union(directories, files), function(item) {
    				return item.data.parent;
    			});
    			result.resolve(tree);
    		});
    	} else {
    		result.resolve({});
    	}
    	return result;
    },
    _searchNodes: function(val, node, args) {
    	var self = this;
    	var result = $.Deferred();
    	var directories_loaded = $.Deferred();
		var files_loaded = $.Deferred();
		this._rpc({
			model: 'muk_dms.directory',
            method: 'name_search',
            kwargs: {
                name: val || "",
                args: this._buildDomain([['parent_directory', 'child_of', node.data.odoo_id]], args.directory.domain),
                operator: args.search.operator || "ilike",
                limit: false,
                context: args.directory.context || session.user_context,
            },
        }).then(function(directories) {
        	directories_loaded.resolve(_.map(directories, function(directory) {
        		return "directory_" + directory[0];
        	}));
        });
		if(args.directoriesOnly) {
			files_loaded.resolve([]);
		} else {
			this._rpc({
				model: 'muk_dms.directory',
	            method: 'search',
	            kwargs: {
	            	args: this._buildDomain([['parent_directory', 'child_of', node.data.odoo_id]]), 
	                context: session.user_context,
	            },
	        }).then(function(ids) {
	        	var search_domain = [['directory', 'in', ids], ['name', args.search.operator || "ilike", val || ""]];
	        	self._rpc({
	        		fields: ['directory'],
	                domain: self._buildDomain(search_domain, args.file.domain),
	                model: 'muk_dms.file',
	                method: 'search_read',
	                context: session.user_context,
	            }).then(function(files) {
	            	files_loaded.resolve(_.map(files, function(file) {
	            		return "directory_" + file.directory[0];
	            	}));
	            }); 
	        });
		}
		$.when(directories_loaded, files_loaded).then(function(directories, files) {
			result.resolve(_.union(directories, files));
		});
    	return result;
    },
    _makeNodeDirectory: function(directory, directoriesOnly) {
    	var has_children;
    	if(directoriesOnly) {
    		has_children = directory.count_directories > 0 ? true : false;
		} else {
			has_children = (directory.count_directories + directory.count_files) > 0 ? true : false;
		}
    	return {
			id: "directory_" + directory.id,
			text: directory.name,
			icon: "fa fa-folder-o",
			type: "directory",
			data: {
				odoo_id: directory.id,
				odoo_model: "muk_dms.directory",
				odoo_record: directory,
				name: directory.name,
				locked: directory.locked,
				perm_read: directory.permission_read,
				perm_create: directory.permission_create && !directory.locked,
				perm_write: directory.permission_write && !directory.locked,
				perm_unlink: directory.permission_unlink && !directory.locked,
				directories: directory.count_directories,
				files: directory.count_files,
				parent: directory.parent_directory ?
						"directory_" + directory.parent_directory[0] : "#",
			},
			children: has_children,
		};
    },
    _makeNodeFile: function(file) {
    	return {
			id: "file_" + file.id,
			text: file.name,
			icon: mimetype.mimetype2fa(file.mimetype, {prefix: "fa fa-"}),
			type: "file",
			data: {
				odoo_id: file.id,
				odoo_model: "muk_dms.file",
				odoo_record: file,
				name: file.name,
				size: utils.format_size(file.size),
				mimetype: file.mimetype,
				extension: file.extension,
				locked: file.locked,
				perm_read: file.permission_read,
				perm_create: file.permission_create && !file.locked,
				perm_write: file.permission_write && !file.locked,
				perm_unlink: file.permission_unlink && !file.locked,
				parent: "directory_" + file.directory[0],
			},
		};
    },
});

return DocumentsModel;

});