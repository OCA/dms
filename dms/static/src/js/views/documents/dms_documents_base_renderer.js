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

odoo.define('muk_dms_views.DocumentsRenderer', function(require) {
"use strict";

var ajax = require('web.ajax');
var core = require('web.core');
var mixins = require('web.mixins');
var config = require('web.config');
var session = require('web.session');
var fieldUtils = require('web.field_utils');

var utils = require('muk_web_utils.common');
var mimetype = require('muk_web_utils.mimetype');

var Widget = require('web.Widget');

var DocumentsRenderer = Widget.extend({
	xmlDependencies: [
		'/muk_dms/static/src/xml/dms_documents_tree.xml'
	],
	cssLibs: [
        '/muk_web_utils/static/lib/jsTree/themes/proton/style.css',
    ],
    jsLibs: [
        '/muk_web_utils/static/lib/jsTree/jstree.js',
    ],
    template: 'muk_dms.DocumentTree',
    events: _.extend({}, Widget.prototype.events, {
		'dragenter .mk_content': '_dragenter_dropzone',
		'dragover .mk_content': '_dragover_dropzone',
		'dragleave .mk_content': '_dragleave_dropzone',
		'drop .mk_content': '_drop_dropzone',
	}),
    init: function (parent, params) {
		this._super.apply(this, arguments);
		this.params = params || {};
    },
    willStart: function() {
        return $.when(ajax.loadLibs(this), this._super.apply(this, arguments));
    },
    start: function() {
    	var self = this;
        if(this.params.dnd) {
        	var dropzone = this.$el.find('.mk_content');
        	dropzone.dndHover().on({
                'dndHoverStart': function(ev) {
                	dropzone.addClass('mk_document_dropzone');
                 	ev.stopPropagation();
                	ev.preventDefault();
                    return false;
                },
                'dndHoverEnd': function(ev) {
                	dropzone.removeClass('mk_document_dropzone');
                	ev.stopPropagation();
                	ev.preventDefault();
                    return false;
                }
            });
    	}
        this.$tree = this.$('.mk_tree');
        this.$tree.jstree(this.params.config);
    	this.$tree.on('open_node.jstree', function (e, data) {
    		if(data.node.data && data.node.data.odoo_model === "muk_dms.directory") {
    			data.instance.set_icon(data.node, "fa fa-folder-open-o"); 
    		}
    	});
    	this.$tree.on('close_node.jstree', function (e, data) { 
    		if(data.node.data && data.node.data.odoo_model === "muk_dms.directory") {
        		data.instance.set_icon(data.node, "fa fa-folder-o"); 
    		}
    	});
    	this.$tree.on('ready.jstree', function (e, data) {
    		self.trigger_up('tree_ready', {
    			data: data
            });
    	});
    	this.$tree.on('changed.jstree', function (e, data) {
    		self.trigger_up('tree_changed', {
    			data: data
            });
    	});
    	this.$tree.on('move_node.jstree', function(e, data) {
    		self.trigger_up('move_node', {
    			node: data.node,
    			new_parent: data.parent,
    			old_parent: data.old_parent,
            });
    	});
    	this.$tree.on('copy_node.jstree', function(e, data) {
    		self.trigger_up('copy_node', {
    			node: data.node,
    			original: data.original,
    			parent: data.parent,
            });
    		
    	});
    	this.$tree.on('rename_node.jstree', function(e, data) {
    		self.trigger_up('rename_node', {
    			node: data.node,
    			text: data.text,
    			old: data.old,
            });
    	});
    	this.$tree.on('delete_node.jstree', function(e, data) {
    		self.trigger_up('delete_node', {
    			node: data.node,
    			parent: data.parent,
            });
    	});
    	this.$('[data-toggle="tooltip"]').tooltip();
        return this._super.apply(this, arguments);
    },
    _dragenter_dropzone: function(ev) {
    	if(this.params.dnd) {
	    	ev.preventDefault();
    	}
    },
    _dragover_dropzone: function(ev) {
    	if(this.params.dnd && ev.originalEvent.dataTransfer) {
        	ev.preventDefault();
    		ev.originalEvent.dataTransfer.dropEffect = 'copy';
    	}
    },
    _dragleave_dropzone: function(ev) {
    	if(this.params.dnd) {
	    	ev.preventDefault();
    	}
    },
    _drop_dropzone: function(ev) {
    	if(this.params.dnd) {
    		ev.stopPropagation();
            ev.preventDefault();
            this.trigger_up('drop_items', {
            	items: ev.originalEvent.dataTransfer.items
            });
    	}
    },
});

return DocumentsRenderer;

});