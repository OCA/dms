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

odoo.define('muk_dms_views.DirectoryFormView', function (require) {
"use strict";

var core = require('web.core');
var registry = require('web.view_registry');

var FormView = require('web.FormView');

var DirectoryFormController = require('muk_dms_views.DirectoryFormController');

var _t = core._t;
var QWeb = core.qweb;

var DirectoryFormView = FormView.extend({
	config: _.extend({}, FormView.prototype.config, {
        Controller: DirectoryFormController,
    }),
});

registry.add('directory_form', DirectoryFormView);

return DirectoryFormView;

});
