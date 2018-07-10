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

odoo.define('muk_dms_dialogs.DocumentInfoDialog', function(require) {
"use strict";

var core = require('web.core');
var session = require('web.session');

var utils = require('muk_web_utils.common');

var Dialog = require('web.Dialog');

var _t = core._t;
var QWeb = core.qweb;

var DocumentInfoDialog = Dialog.extend({
	init: function (parent, options) {
    	this.options = options || {};
        this._super(parent, _.extend({}, {
            size: "medium",
        }, this.options));
    },
    willStart: function() {
    	var self = this;
    	var load = this._rpc({
            fields: this.options.fields,
            domain: [['id', '=', this.options.id]],
            model: this.options.model,
            method: 'search_read',
            context: this.options.context || session.user_context,
        }).then(function(records) {
        	self.record = records[0];
        	if(self.record.size) {
        		self.record.size = utils.format_size(self.record.size);
        	}
        	if(self.record.write_uid) {
        		self.record.write_uid = self.record.write_uid[1];
        	}
        	self.$content = $(QWeb.render(self.options.qweb, {
        		widget: self,
        		record: self.record,
			}));
        });
        return $.when(this._super.apply(this, arguments), load);
    },
});

return DocumentInfoDialog;

});