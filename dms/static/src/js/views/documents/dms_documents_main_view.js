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

odoo.define('muk_dms_views.DocumentsMainView', function(require) {
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

var Widget = require('web.Widget');
var Dialog = require('web.Dialog');

var DocumentTreeView = require('muk_dms_views.DocumentTreeView');
var PreviewHelper = require('muk_dms_preview_file.PreviewHelper');

var _t = core._t;
var QWeb = core.qweb;

var DocumentTreeMainView = DocumentTreeView.extend({
	cssLibs: [
        '/muk_web_utils/static/lib/jquery-splitter/css/jquery.splitter.css',
    ],
    jsLibs: [
        '/muk_web_utils/static/lib/jquery-splitter/js/jquery.splitter.js',
    ],
    custom_events: _.extend({}, DocumentTreeView.prototype.custom_events, {
    	tree_ready: '_treeReady',
    	tree_changed: '_treeChanged',
    }),
	template: 'muk_dms.DocumentTreeView',
	init: function(parent) {
        this._super(parent, _.extend({}, {
        	key: "dms_documents",
	    }));
        this.controller.params.action_open_dialog = this._get_storage('dms_documents_open_dialog', true);
    },
    willStart: function() {
        return $.when(ajax.loadLibs(this), this._super.apply(this, arguments));
    },
    toggle_dialog: function() {
    	var open_dialog = !this._get_storage('dms_documents_open_dialog', true);
    	this.controller.params.action_open_dialog = open_dialog;
    	this._set_storage('dms_documents_open_dialog', open_dialog);        
    	this._display_open_dialog();
    },
    toggle_refresh: function() {
    	var auto_refresh = !this._get_storage('dms_documents_auto_refresh', true);
        this._set_storage('dms_documents_auto_refresh', auto_refresh);
        this._display_auto_refresh();
    },
    show_preview: function() {
    	if(!this.$switch_buttons.parent().find('.mk_show_preview').hasClass("active")) {
        	this.$switch_buttons.parent().find('.mk_show_preview').addClass("active");
        	this.$switch_buttons.parent().find('.mk_hide_preview').removeClass("active");
    		this.$el.find('.mk_document_col_preview').show();
        	this.splitter = this.$el.find('.mk_document_row').split({
        	    orientation: 'vertical',
        	    limit: 100,
        	    position: '60%'
        	});
    	}
    	this._set_storage('dms_documents_disable_preview', false);
    },
    hide_preview: function() {
    	if(!this.$switch_buttons.parent().find('.mk_hide_preview').hasClass("active")) {
    		this.$switch_buttons.parent().find('.mk_hide_preview').addClass("active");
    		this.$switch_buttons.parent().find('.mk_show_preview').removeClass("active");
    		this.$el.find('.mk_document_col_preview').hide();
    		this.$el.find('.mk_document_col_tree').width('100%');
    		if(this.splitter) {
    			this.splitter.destroy();
    		}
    		this.splitter = false;
    	}
    	this._set_storage('dms_documents_disable_preview', true);
    },
    refresh: function(message) {
    	if(this._get_storage('dms_documents_auto_refresh', true)) {
    		this.controller.refresh(message);
    	}
    },
    _get_storage: function(key, bool) {
    	var value = this.call('local_storage', 'getItem', key);
    	if(bool) {
    		return value === 'true';
    	} else {
    		return value;
    	}
    },
    _set_storage: function(key, value) {
    	this.call('local_storage', 'setItem', key, value);
    },
    _display_open_dialog: function() {
    	var open_dialog = this._get_storage('dms_documents_open_dialog', true);
    	if(open_dialog) {
    		this.$pager.find('.mk_action_dialog').addClass("active");
    	} else {
    		this.$pager.find('.mk_action_dialog').removeClass("active");
    	}
    },
    _display_auto_refresh: function() {
    	var auto_refresh = this._get_storage('dms_documents_auto_refresh', true);
    	if(auto_refresh) {
    		this.$pager.find('.mk_auto_refresh').addClass("active");
        	this.$pager.find('.mk_refresh').prop("disabled", false);
    	} else {
    		this.$pager.find('.mk_auto_refresh').removeClass("active");
        	this.$pager.find('.mk_refresh').prop("disabled", true);
    	}
    },
    _update_cp: function() {
    	var self = this;
    	if (!this.$buttons) {
            this.$buttons = $(QWeb.render('muk_dms.DocumentTreeViewButtons', {
                widget: this,
            }));
            this.$buttons.find('.mk_open').on('click', _.bind(this._open_selected_node, this));
            this.$buttons.find('.mk_create').on('click', _.bind(this._create_selected_node, this));
            this.$buttons.find('.mk_edit').on('click', _.bind(this._edit_selected_node, this));
            this.$buttons.find('.mk_delete').on('click', _.bind(this._delete_selected_node, this));
        }
    	if (!this.$pager) {
            this.$pager = $(QWeb.render('muk_dms.DocumentTreeViewActions', {
                widget: this,
            }));
            this.$pager.find('.mk_action_help').on('click', _.bind(this._show_help, this));
            this.$pager.find('.mk_refresh').on('click', _.bind(this.refresh, this));
            this.$pager.find('.mk_auto_refresh').on('click', _.bind(this.toggle_refresh, this));
            this.$pager.find('.mk_action_dialog').on('click', _.bind(this.toggle_dialog, this));
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
            this.$searchview.find('#mk_searchview_input').keyup(this._trigger_search.bind(this));
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
        this.$switch_buttons.parent().find('.mk_show_preview').on('click', _.bind(this.show_preview, this));
        this.$switch_buttons.parent().find('.mk_hide_preview').on('click', _.bind(this.hide_preview, this));
        this._display_open_dialog();
        this._display_auto_refresh();
    },
    _update_view: function() {
    	var self = this;
    	this.controller.appendTo(this.$('.mk_document_col_tree'));
    },    
    _treeReady: function(ev) {
    	if(!config.device.isMobile && !this._get_storage('dms_documents_disable_preview', true)) {
			this.show_preview();
		} else {
			this.hide_preview();
		}
    },
    _treeChanged: function(ev) {
    	var data = ev.data.data;
    	if(data.selected && data.selected.length === 1) {
			if(!this._get_storage('dms_documents_disable_preview', true)) {
				this._preview_node(data.node);
			}
			this.$buttons.find('button.mk_open').prop('disabled', !data.node.data.perm_read);
			this.$buttons.find('button.mk_create').prop('disabled', !data.node.data.perm_create);
			this.$buttons.find('button.mk_edit').prop('disabled', !data.node.data.perm_write);
			this.$buttons.find('button.mk_delete').prop('disabled', !data.node.data.perm_unlink);
		} else if(data.selected && data.selected.length > 1) {
			this.$buttons.find('button.mk_open').prop('disabled', true);
			this.$buttons.find('button.mk_create').prop('disabled', true);
			this.$buttons.find('button.mk_edit').prop('disabled', true);
			this.$buttons.find('button.mk_delete').prop('disabled', !data.node.data.perm_unlink);
		} else {
			this.$buttons.find('button.mk_open').prop('disabled', true);
			this.$buttons.find('button.mk_create').prop('disabled', true);
			this.$buttons.find('button.mk_edit').prop('disabled', true);
			this.$buttons.find('button.mk_delete').prop('disabled', true);
		}
    },
    _preview_node: function(node) {
    	var self = this;
    	if(node.data && node.data.odoo_model === "muk_dms.file") {
    		PreviewHelper.createFilePreviewContent(node.data.odoo_id, self).then(function($content) {
    			self.$el.find('.mk_document_preview').html($content);
    		});
    	} else if(node.data && node.data.odoo_model === "muk_dms.directory") {
    		self.$el.find('.mk_document_preview').html(
    				$(QWeb.render('muk_dms.DocumentTreeViewDirectoryPreview', {
			            widget: this,
			            directory: node.data,
    				})));
    	}
    },
    _open_selected_node: function() {
    	var node = this.controller.getSelectedItem();
    	if(node) {
    		this.controller._openNode(node);
    	}
    },
    _create_selected_node: function() {
    	var node = this.controller.getSelectedItem();
    	if(node) {
    		var parent = node.data.odoo_model === "muk_dms.file" ? this.controller.getParentNode(node) : node;
    		this.controller._createNode(parent, node.data.odoo_model);
    	}
    },
    _edit_selected_node: function() {
    	var node = this.controller.getSelectedItem();
    	if(node) {
    		this.controller._editNode(node);
    	}
    },
    _delete_selected_node: function() {
    	var nodes = this.controller.getTopSelectedItems();
    	if(nodes.length > 0) {
    		this.controller._deleteNodes(nodes);
    	}
    },
    _show_help: function() {
        var buttons = [{
            text: _t("Ok"),
            close: true,
        }];
    	var dialog = new Dialog(this, {
            size: 'medium',
            buttons: buttons,
            $content: $(QWeb.render('muk_dms.DocumentHelpDialogContent')),
            title: _t("Help"),
        });
    	dialog.open();
    },
});

core.action_registry.add('muk_dms_views.documents', DocumentTreeMainView);

return DocumentTreeMainView;

});