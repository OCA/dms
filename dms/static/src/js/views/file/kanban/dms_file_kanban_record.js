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

odoo.define('muk_dms_views.FileKanbanRecord', function (require) {
"use strict";

var core = require('web.core');
var ajax = require('web.ajax');
var session = require('web.session');

var KanbanRecord = require('web.KanbanRecord');

var PreviewHelper = require('muk_dms_preview_file.PreviewHelper');

var _t = core._t;
var QWeb = core.qweb;

var FileKanbanRecord = KanbanRecord.extend({
	events: _.extend({}, KanbanRecord.prototype.events, {
		'click .mk_dms_file_thumbnail': '_onImageClicked',
    }),
    _onImageClicked: function(e) {
    	e.preventDefault();
    	e.stopPropagation();
        PreviewHelper.createFilePreviewDialog($(e.currentTarget).data('id'), this);
    },
});

return FileKanbanRecord;

});
