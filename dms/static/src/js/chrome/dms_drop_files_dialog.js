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

odoo.define('muk_dms_dialogs.DocumentDropFilesDialog', function(require) {
"use strict";

var ajax = require('web.ajax');
var core = require('web.core');
var session = require('web.session');

var utils = require('muk_web_utils.common');

var DocumentDropDialog = require('muk_dms_dialogs.DocumentDropDialog');

var _t = core._t;
var QWeb = core.qweb;

var DocumentDropFilesDialog = DocumentDropDialog.extend({
	init: function (parent, options) {
    	this.options = options || {};
    	this._super(parent, _.extend({}, {
            title: _t("Upload Files into: ") + this.options.name || "",
            save: _t("Upload"),
            $form: "#mk_document_upload",
            $content: $(QWeb.render("muk_dms.DocumentDropFilesDialog", {
            	url: "/dms/upload/file/" + this.options.id,
            	csrf_token:	core.csrf_token,
            })),
            dropzone: {
            	maxFiles: 25,
            	parallelUploads: 25,
            	init: function() {
            		this.on("addedfile", function() {
            			if (this.files[25] != null){
            				this.removeFile(this.files[0]);
            			}
            		});
            	}
            }
        }, this.options));
    },
});

return DocumentDropFilesDialog;

});