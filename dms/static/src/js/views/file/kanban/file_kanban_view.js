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

odoo.define('muk_dms.FileKanbanView', function (require) {
"use strict";

var core = require('web.core');
var registry = require('web.view_registry');

var KanbanView = require('web.KanbanView');

var FileKanbanModel = require('muk_dms.FileKanbanModel');
var FileKanbanRenderer = require('muk_dms.FileKanbanRenderer');
var FileKanbanController = require('muk_dms.FileKanbanController');
var FileSearchPanel = require('muk_dms.FileSearchPanel');

var _t = core._t;
var QWeb = core.qweb;

var FileKanbanView = KanbanView.extend({
	config: _.extend({}, KanbanView.prototype.config, {
		Renderer: FileKanbanRenderer,
        Controller: FileKanbanController,
        Model: FileKanbanModel,
		SearchPanel: FileSearchPanel,
    }),
});

registry.add('file_kanban', FileKanbanView);

return FileKanbanView;

});
