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

odoo.define('muk_dms_views.FileKanbanColumn', function (require) {
"use strict";

var core = require('web.core');
var ajax = require('web.ajax');
var session = require('web.session');

var KanbanColumn = require('web.KanbanColumn');

var FileKanbanRecord = require('muk_dms_views.FileKanbanRecord');

var _t = core._t;
var QWeb = core.qweb;

var FileKanbanColumn = KanbanColumn.extend({
	addRecord: function (recordState, options) {
        var record = new FileKanbanRecord(this, recordState, this.record_options);
        this.records.push(record);
        if (options && options.position === 'before') {
            record.insertAfter(this.quickCreateWidget ? this.quickCreateWidget.$el : this.$header);
        } else {
            var $load_more = this.$('.o_kanban_load_more');
            if ($load_more.length) {
                record.insertBefore($load_more);
            } else {
                record.appendTo(this.$el);
            }
        }
    },
});

return FileKanbanColumn;

});
