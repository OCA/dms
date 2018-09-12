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

odoo.define('muk_dms.FileFormController', function (require) {
"use strict";

var core = require('web.core');
var ajax = require('web.ajax');
var session = require('web.session');

var FormController = require('web.FormController');

var _t = core._t;
var QWeb = core.qweb;

var FileFormController = FormController.extend({
	createRecord: function (parentID) {
        var record = this.model.get(this.handle, {raw: true});
        var context = _.extend({}, record.getContext(), {
        	default_directory: record.data.directory,
        });
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
        	this.handle = handle;
            this._updateEnv();
            return this._setMode('edit');
        }.bind(this));
    },
});

return FileFormController;

});
