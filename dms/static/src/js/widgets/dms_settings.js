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

odoo.define('muk_dms_widgets.settings', function(require) {
"use strict";

var core = require('web.core');
var session = require('web.session');
var registry = require('web.field_registry');
var field_utils = require('web.field_utils');
var field_widgets = require('web.relational_fields');

var _t = core._t;
var QWeb = core.qweb;

var FieldSettingsMany2One = field_widgets.FieldMany2One.extend({
	willStart: function () {
		var self = this;
		var check_user = session.user_has_group('muk_dms.group_dms_manager').then(function(check) {
	    	self.nodeOptions.no_open = !check;
	    });
		return $.when(this._super.apply(this, arguments), check_user);
	},
});

registry.add('dms_settings', FieldSettingsMany2One);

return FieldSettingsMany2One;

});
