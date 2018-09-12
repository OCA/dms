/**********************************************************************************
*
*    Copyright (c) 2017-2019 MuK IT GmbH.
*
*    This file is part of MuK Documents 
*    (see https://mukit.at).
*
*    This program is free software: you can redistribute it and/or modify
*    it under the terms of the GNU Lesser General Public License as published by
*    the Free Software Foundation, either version 3 of the License, or
*    (at your option) any later version.
*
*    This program is distributed in the hope that it will be useful,
*    but WITHOUT ANY WARRANTY; without even the implied warranty of
*    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
*    GNU Lesser General Public License for more details.
*
*    You should have received a copy of the GNU Lesser General Public License
*    along with this program. If not, see <http://www.gnu.org/licenses/>.
*
**********************************************************************************/

odoo.define('muk_dms.FileKanbanRenderer', function (require) {
"use strict";

var core = require('web.core');
var config = require('web.config');
var session = require('web.session');

var dropzone = require('muk_web_utils.dropzone');

var KanbanRenderer = require('web.KanbanRenderer');
var FileKanbanRecord = require('muk_dms.FileKanbanRecord');

var _t = core._t;
var QWeb = core.qweb;

var FileKanbanRenderer = KanbanRenderer.extend(dropzone.FileDropzoneMixin, {
	config: _.extend({}, KanbanRenderer.prototype.config, {
        KanbanRecord: FileKanbanRecord,
    }),
	start: function () {
    	var res = this._super.apply(this, arguments);
		this._startDropzone(this.$el);
        return res;
    },
	destroy: function () {
		var res = this._super.apply(this, arguments);
		this._destroyDropzone(this.$el);
        return res;
    },
    _handleDrop: function(event) {
    	var dataTransfer = event.originalEvent.dataTransfer;
    	if (dataTransfer.items && dataTransfer.items.length > 0) {
    		this.trigger_up('upload_files', {
            	items: dataTransfer.items
            });
    	}
	},
});

return FileKanbanRenderer;

});
