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

odoo.define('muk_dms_dialogs.DocumentFileSelectionDialog', function(require) {
"use strict";

var core = require('web.core');

var DocumentSelectionDialog = require('muk_dms_dialogs.DocumentSelectionDialog');
var DocumentTreeDialogView = require('muk_dms_views.DocumentTreeDialogView');

var _t = core._t;
var QWeb = core.qweb;

var DocumentFileSelectionDialog = DocumentSelectionDialog.extend({
	default_options: {
        view: {
        	view: DocumentTreeDialogView,
        	options: {
	        	key: "dms_files_finder",
	        	disable_multiple: true,
	        	contextmenu: false,
        		filesOnly: true,
	        	model: {
	        		noSettings: true,
	        	}
	        },
        }
    },
	init: function (parent, options) {
		this._super(parent, _.extend({}, this.default_options, options));
	}
});

return DocumentFileSelectionDialog;

});