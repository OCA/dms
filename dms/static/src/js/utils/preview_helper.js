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

odoo.define('muk_dms_preview_file.PreviewHelper', function (require) {
"use strict";

var core = require('web.core');
var session = require('web.session');

var PreviewGenerator = require('muk_preview.PreviewGenerator');
var PreviewDialog = require('muk_preview.PreviewDialog');

var QWeb = core.qweb;
var _t = core._t;

var PreviewHelper = core.Class.extend({
	createFilePreviewDialog: function(id, widget) {
		widget._rpc({
            fields: ['name', 'mimetype', 'extension'],
            domain: [['id', '=', id]],
            model: 'muk_dms.file',
            method: 'search_read',
            limit: 1,
            context: session.user_context,
        }).then(function(files) {
        	var file = files.length > 0 ? files[0] : null;
        	var download_url = '/web/content?' + $.param({
        		model: 'muk_dms.file',
    			filename: file.name,
    			filename_field: 'name',
    			field: 'content',
    			id: file.id,
    			download: true
            });
			PreviewDialog.createPreviewDialog(self, download_url,
				file.mimetype, file.extension, file.name);
		});
	},
	createFilePreviewContent: function(id, widget) {
		return widget._rpc({
	            fields: ['name', 'mimetype', 'extension'],
	            domain: [['id', '=', id]],
	            model: 'muk_dms.file',
	            method: 'search_read',
	            limit: 1,
	            context: session.user_context,
	        }).then(function(files) {
	        	var file = files.length > 0 ? files[0] : null;
	        	var download_url = '/web/content?' + $.param({
	        		model: 'muk_dms.file',
	    			filename: file.name,
	    			filename_field: 'name',
	    			field: 'content',
	    			id: file.id,
	    			download: true
	            });
				return PreviewGenerator.createPreview(self, download_url,
					file.mimetype, file.extension, file.name);
			});
	}
});

PreviewHelper.createFilePreviewDialog = function(id, widget) {
    return new PreviewHelper().createFilePreviewDialog(id, widget);
};

PreviewHelper.createFilePreviewContent = function(id, widget) {
    return new PreviewHelper().createFilePreviewContent(id, widget);
};

return PreviewHelper;

});