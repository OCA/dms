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

odoo.define('muk_dms_client_refresh.channel', function (require) {
"use strict";

var WebClient = require('web.WebClient');
var session = require('web.session');	
var bus = require('bus.bus');	

WebClient.include({
    refresh: function(message) {
    	this._super.apply(this, arguments);
    	var action = this.action_manager && this.action_manager.inner_action;
    	var widget = this.action_manager && this.action_manager.inner_widget;
    	if(session.uid !== message.uid && widget && action && 
    			action.action_descr.tag === "muk_dms_views.documents" && (
    			message.model === 'muk_dms.directory' ||
    			message.model === 'muk_dms.file')) {
    		widget.refresh(message);
    	}
    },
});

});
