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

odoo.define('muk_dms.FileKanbanController', function (require) {
"use strict";

var core = require('web.core');
var session = require('web.session');

var utils = require('muk_web_utils.files');
var async = require('muk_web_utils.async');

var Domain = require('web.Domain');
var KanbanController = require('web.KanbanController');

var FileUpload = require('muk_dms_mixins.FileUpload');

var _t = core._t;
var QWeb = core.qweb;

var FileKanbanController = KanbanController.extend(FileUpload, {
	custom_events: _.extend({}, KanbanController.prototype.custom_events, {
		upload_files: '_onUploadFiles',
    }),
    _getSelectedDirectory: function () {
        var record = this.model.get(this.handle, {raw: true});
        var directoryID = this._searchPanel.getSelectedDirectory();
    	var context = record.getContext();
    	if (directoryID) {
    		return directoryID;
    	} else if (context.active_model === "muk_dms.directory") {
    		return context.active_id;
    	}
    },
	_onUploadFiles: function(event) {
		var directoryID = this._getSelectedDirectory();
		if (directoryID) {
			utils.getFileTree(event.data.items, true).then(
				this._uploadFiles.bind(this, directoryID) 
			);
		} else {
			this.do_warn(_t("Upload Error"), _t("No Directory has been selected!"));
		}
	},
});

return FileKanbanController;

});
