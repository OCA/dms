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

odoo.define('muk_dms_mixins.FileUpload', function (require) {

var core = require('web.core');
var session = require('web.session');

var utils = require('muk_web_utils.files');
var async = require('muk_web_utils.async');

var _t = core._t;
var QWeb = core.qweb;
	
var FileUploadMixin = {
    _uploadFile: function(file, directory) {
    	var def = $.Deferred();
    	utils.readFile(file, function (upload) {
	        this._rpc({
	            model: 'muk_dms.file',
	            method: 'create',
	            args: [{
	                'name': file.name,
	                'directory': directory,
	                'content': upload.target.result.split(',')[1],
	            }],
	            context: session.user_context
	        }).then(function (result) {
	        	def.resolve(result);
	        });
    	}.bind(this));
    	return def;
    },
    _createUploadDirectory: function(name, parent_id) {
    	return this._rpc({
            model: 'muk_dms.directory',
            method: 'create',
            args: [{
            	'name': name,
            	'parent_directory': parent_id,
            }],
            context: session.user_context,
    	});
    },
    _createUploadNotification: function() {
    	return this.call('notification', 'notify', {
            title: _t('Upload Files'), 
            message: _t('Uploading...'),
            icon: 'fa-upload', 
            sticky: true,
            progress: {
            	text: "0%",
            	state: 0.0,
            },
        });
    },
    _updateUploadNotification: function(notification, progress) {
    	this.call('notification', 'progress', notification, {
        	text: (progress * 100).toFixed(2) + "%",
        	state: (progress * 100).toFixed(2),
        });
    },
    _closeUploadNotification: function(notification) {
    	this.call('notification', 'close', notification);
    },
    _uploadFiles: function(directory, tree) {
    	var progress = 0;
    	var notification = this._createUploadNotification();
    	var upload = function(parent_id, item) {
    		var def = $.Deferred();
    		if(item.isFile || item.isFileItem) {
    			this._uploadFile(item, parent_id).then(function(res) {
    				this._updateUploadNotification(notification, ++progress / tree.count);
    				def.resolve(res);
    			}.bind(this));
    		} else if(item.isDirectory) {
    			this._createUploadDirectory(item.name, parent_id).then(function(id) {
    				async.syncLoop(
    					item.files,
    					upload.bind(this, id),
    					function(res) {
    						def.resolve(id);
    					}
			    	);
    			}.bind(this));
    		}
    		return def;
	    };
	    var finish = function() {
	    	this._closeUploadNotification(notification);
	    	this.reload();
	    };
    	async.syncLoop(
    		tree.files, 
    		upload.bind(this, directory),
    		finish.bind(this),
    	);
    },
};

return FileUploadMixin;

});
