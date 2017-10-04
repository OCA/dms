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
odoo.define('muk_dms_views.file', function(require) {
"use strict";

var core = require('web.core');
var ajax = require('web.ajax');
var session = require('web.session');

var FormController = require('web.FormController');
var ListRenderer = require('web.ListRenderer');
var KanbanRecord = require('web.KanbanRecord');

var PreviewHelper = require('muk_dms_preview_file.PreviewHelper');

var QWeb = core.qweb;
var _t = core._t;

FormController.include({
	createRecord: function (parentID) {
		if(this.modelName === 'muk_dms.file') {
			var self = this;
	        var record = this.model.get(this.handle, {raw: true});
	        var context = record.getContext();
	        context.default_directory = record.data.directory;
	        return this.model.load({
	            context: context,
	            fields: record.fields,
	            fieldsInfo: record.fieldsInfo,
	            modelName: this.modelName,
	            parentID: parentID,
	            res_ids: record.res_ids,
	            type: 'record',
	            viewType: 'form',
	        }).then(function (handle) {
	            self.handle = handle;
	            self._updateEnv();
	            return self._setMode('edit');
	        });
		} else {
			this._super.apply(this, arguments);
		}
    },
    _updateButtons: function () {
    	this._super.apply(this, arguments);
    	if(this.$buttons && this.modelName === 'muk_dms.file') {
    		var actions = this.updateActions;
    		var data = this.model.get(this.handle).data;
    		var $create = this.$buttons.find('.o_form_button_create');
    		var $edit = this.$buttons.find('.o_form_button_edit');
    		if(actions) {
    			$create.toggle(!!actions.create);
    			$edit.toggle(!!actions.edit);
    		}
    		if(!data.editor && data.locked &&
					data.locked instanceof Object) {
				var $edit = this.$buttons.find('.o_form_button_edit');
				$edit.prop("disabled", true);
				$edit.text(_t("Locked!"));
			} else {
				var $edit = this.$buttons.find('.o_form_button_edit');
				$edit.prop("disabled", false);
				$edit.text(_t("Edit"));
			}
    	}
    },
    _updateSidebar: function () {
    	this._super.apply(this, arguments);
    	if(this.sidebar && this.modelName === 'muk_dms.file') {
    		var actions = this.updateActions;
    		var $delete = this.sidebar.$el.find(
    			'li > a[data-section="other"]:contains("' + _t('Delete') + '")'
    		);
			var $duplicate = this.sidebar.$el.find(
				'li > a[data-section="other"]:contains("' + _t('Duplicate') + '")'
			);
			if(actions) {
				$delete.toggle(!!actions.delete);
				$duplicate.toggle(!!actions.duplicate);
    		}
    	}
    	
    },
    _update: function() {
    	if(this.modelName === 'muk_dms.file') {
	    	var data = this.model.get(this.handle).data;
	    	this.updateActions = {
				create: !!data.perm_create,
				edit: !!data.perm_write,
				delete: !!data.perm_unlink,
				duplicate: !!data.perm_create,
	    	}
    	}
    	return this._super.apply(this, arguments);
    },
});

ListRenderer.include({
	_setDecorationClasses: function (record, $tr) {
		this._super.apply(this, arguments);
		if(record.model === 'muk_dms.file') {
			if(record.data.locked && 
					record.data.locked instanceof Object) {
				$tr.addClass("locked");
			} else {
				$tr.removeClass("locked");
			}
			if(!record.data.perm_unlink) {
				$tr.addClass("no_unlink");
			} else {
				$tr.removeClass("no_unlink");
			}
		}
	},
});

KanbanRecord.include({
	start: function() {
		var self = this;
		this._super.apply(this, arguments);
		if (this.modelName === 'muk_dms.file') {
			this.$(".muk_image").click(function(e) {
				e.stopPropagation();
		        PreviewHelper.createFilePreviewDialog($(e.currentTarget).data('id'), self);
			});
			this.$(".muk_filename").click(function(e) {
				e.stopPropagation();
				self._openRecord();
			});
		}
	}
});

});