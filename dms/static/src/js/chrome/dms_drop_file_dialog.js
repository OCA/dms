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

odoo.define('muk_dms_dialogs.DocumentDropFileDialog', function(require) {
"use strict";

var ajax = require('web.ajax');
var core = require('web.core');
var session = require('web.session');

var utils = require('muk_web_utils.common');

var DocumentDropDialog = require('muk_dms_dialogs.DocumentDropDialog');

var _t = core._t;
var QWeb = core.qweb;

var DocumentDropFileDialog = DocumentDropDialog.extend({
	init: function (parent, options) {
    	this.options = options || {};
    	var buttons = [{
            text:  _t("Replace File"),
            classes: 'btn-primary',
            close: true,
            click: this._save.bind(this),
        }, {
            text: _t("Replace Content"),
            classes: 'btn-primary',
            close: true,
            click: this._replace.bind(this),
        }, {
            text: _t("Cancel"),
            close: true,
        }];
    	this._super(parent, _.extend({}, {
            title: _t("Replace File: ") + this.options.name || "",
            buttons: buttons,
            $form: "#mk_document_replace",
            $content: $(QWeb.render("muk_dms.DocumentDropFileDialog", {
            	url: "/dms/replace/file/" + this.options.id,
            	csrf_token:	core.csrf_token,
            })),
            dropzone: {
            	maxFiles: 1,
            	init: function() {
            		this.on("addedfile", function() {
            			if (this.files[1] != null){
            				this.removeFile(this.files[0]);
            			}
            		});
            	}
            },
        }, this.options));
    },
    _replace: function() {
    	var dropzone = this.dropzone.get(0).dropzone;
    	dropzone.options.params = {
    		content_only: true,
    	};
    	dropzone.processQueue();
    },
});

return DocumentDropFileDialog;

});