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

odoo.define('muk_dms_views.FileKanbanController', function (require) {
"use strict";

var core = require('web.core');
var session = require('web.session');

var KanbanController = require('web.KanbanController');

var _t = core._t;
var QWeb = core.qweb;

var FileKanbanController = KanbanController.extend({
    custom_events: _.extend({}, KanbanController.prototype.custom_events, {
    	select_direcotry: '_selectDirecotry',
    }),
    _selectDirecotry: function(ev) {
    	this.do_action({
    		type: 'ir.actions.act_window',
    		name: ev.data.name + _t('/Files'),
            res_model: "muk_dms.file",
            view_type: 'form',
            view_mode: 'form',
            views: [
            	[false, 'kanban'],
            	[false, 'list'], 
            	[false, 'graph'], 
            	[false, 'pivot'], 
            	[false, 'form']
            ],
            domain: [
        		["directory", "=",  ev.data.id],
        		["show_tree", "=",  'True']
        	],
        	context: _.extend({}, session.user_context, {
        		'default_directory': ev.data.id,
        		'mail_create_nolog': 'True',
        	}),
        });
    }
});

return FileKanbanController;

});
