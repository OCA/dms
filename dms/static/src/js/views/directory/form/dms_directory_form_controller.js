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

odoo.define('muk_dms_views.DirectoryFormController', function (require) {
"use strict";

var core = require('web.core');
var ajax = require('web.ajax');
var session = require('web.session');

var FormController = require('web.FormController');

var _t = core._t;
var QWeb = core.qweb;

var DirectoryFormController = FormController.extend({
	createRecord: function (parentID) {
		var self = this;
        var record = this.model.get(this.handle, {raw: true});
        var context = record.getContext();
        context.default_parent_directory = record.data.id;
        return this.model.load({
            context: context,
            fields: record.fields,
            fieldsInfo: record.fieldsInfo,
            modelName: this.modelName,
            parentID: parentID,
            res_ids: record.res_ids,
            type: 'record',
            viewType: 'form',
        }).then(function (handle) {
            self.handle = handle;
            self._updateEnv();
            return self._setMode('edit');
        });
    },
});

return DirectoryFormController;

});
