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

odoo.define('muk_dms_views.FileKanbanRenderer', function (require) {
"use strict";

var core = require('web.core');
var ajax = require('web.ajax');
var config = require('web.config');
var session = require('web.session');
var quick_create = require('web.kanban_quick_create');

var KanbanRenderer = require('web.KanbanRenderer');
var ColumnQuickCreate = quick_create.ColumnQuickCreate;

var FileKanbanColumn = require('muk_dms_views.FileKanbanColumn');
var FileKanbanRecord = require('muk_dms_views.FileKanbanRecord');

var _t = core._t;
var QWeb = core.qweb;

var FileKanbanRenderer = KanbanRenderer.extend({
	willStart: function () {
		var load_sidebar = this._load_kanban_sidebar_data();
        return $.when(this._super.apply(this, arguments), load_sidebar);
    },
	updateColumn: function (localID, columnState, options) {
        var newColumn = new FileKanbanColumn(this, columnState, this.columnOptions, this.recordOptions);
        var index = _.findIndex(this.widgets, {db_id: localID});
        var column = this.widgets[index];
        this.widgets[index] = newColumn;
        return newColumn.insertAfter(column.$el).then(function () {
            if (options && options.openQuickCreate) {
                newColumn.addQuickCreate();
            }
            column.destroy();
        });
    },
	_renderUngrouped: function (fragment) {
        var self = this;
        _.each(this.state.data, function (record) {
            var kanbanRecord = new FileKanbanRecord(self, record, self.recordOptions);
            self.widgets.push(kanbanRecord);
            kanbanRecord.appendTo(fragment);
        });
        this._renderGhostDivs(fragment, 6);
    },
    _renderGrouped: function (fragment) {
        var self = this;
        _.each(this.state.data, function (group) {
            var column = new FileKanbanColumn(self, group, self.columnOptions, self.recordOptions);
            if (!group.value) {
                column.prependTo(fragment);
                self.widgets.unshift(column);
            } else {
                column.appendTo(fragment);
                self.widgets.push(column);
            }
        });
        if(this.$el.sortable('instance') !== undefined) {
            this.$el.sortable('destroy');
        }
        if (this.groupedByM2O) {
            this.$el.sortable({
                axis: 'x',
                items: '> .o_kanban_group',
                handle: '.o_kanban_header_title',
                cursor: 'move',
                revert: 150,
                delay: 100,
                tolerance: 'pointer',
                forcePlaceholderSize: true,
                stop: function () {
                    var ids = [];
                    self.$('.o_kanban_group').each(function (index, u) {
                        if (_.isNumber($(u).data('id'))) {
                            ids.push($(u).data('id'));
                        }
                    });
                    self.trigger_up('resequence_columns', {ids: ids});
                },
            });
            if (this.createColumnEnabled) {
                this.quickCreate = new ColumnQuickCreate(this);
                this.quickCreate.appendTo(fragment);
            }
        }
    },
    _renderView: function () {
    	var self = this;
    	this.$el.parent().find('.mk_dms_file_sidebar').remove();
    	if(!config.device.isMobile && _.some(_.keys(this.kanban_sidebar), function(key) {
    		return !(!self.kanban_sidebar[key] || _.isEmpty(self.kanban_sidebar[key]));
    	})) {
    		this.sidebar = $("<div>", {
	    		class: "mk_dms_file_sidebar",
	    		html: $(QWeb.render('muk_dms.KanbanFileSidebar', {
	                widget: this,
	                data: this.kanban_sidebar,
	            })),
	    	});
    		this.sidebar.find('.mk_dms_file_sidebar_directories a').on(
    				'click', _.bind(this._select_direcotry, this));
	    	this.$el.before(this.sidebar);
	    	var context = this.state.getContext();
	    	if (context.default_directory) {
	    		this.sidebar.find("#directory_" + 
	    				context.default_directory).addClass('active');
	    	}
    	}
        return this._super.apply(this, arguments);
    },
    _load_kanban_sidebar_data: function() {
    	var self = this;
    	return this._rpc({
            fields: ['name', 'count_files', 'permission_create'],
            domain: [['starred', '=', 'True']],
            model: 'muk_dms.directory',
            method: 'search_read',
            context: session.user_context,
        }).then(function(result) {
        	self.kanban_sidebar = {
        		starred: result,
        	}
        });
    },
    _select_direcotry: function(ev) {
    	this.trigger_up('select_direcotry', {
    		id: $(ev.currentTarget).data('id'),
    		name: $(ev.currentTarget).data('name'),
    	});
    },
});

return FileKanbanRenderer;

});
