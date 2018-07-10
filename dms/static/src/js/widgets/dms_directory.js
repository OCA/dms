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

odoo.define('muk_dms_widgets.directory', function(require) {
"use strict";

var core = require('web.core');
var session = require('web.session');
var registry = require('web.field_registry');
var field_utils = require('web.field_utils');
var field_widgets = require('web.relational_fields');

var DocumentDirectorySelectionDialog = require('muk_dms_dialogs.DocumentDirectorySelectionDialog');

var _t = core._t;
var QWeb = core.qweb;

var FieldDirectoryMany2One = field_widgets.FieldMany2One.extend({
	willStart: function () {
		var self = this;
		if(this.value) {
			var check_permission = this._rpc({
		        fields: ['name', 'path', 'permission_read'],
		        domain: [['id', '=', self.value.data.id]],
		        model: 'muk_dms.directory',
		        method: 'search_read',
		        limit: 1,
		        context: session.user_context,
		    }).then(function(directories) {
		    	self.directory = directories.length > 0 ? directories[0] : null;
		    	self.nodeOptions.no_open = self.directory ? !self.directory.permission_read : true;
		    });
			return $.when(this._super.apply(this, arguments), check_permission);
		} else {
			return this._super.apply(this, arguments);
		}
	},
	_render: function () {
        this._super.apply(this, arguments);
    	this._renderTooltip();
    },
    _renderTooltip: function () {
    	if(this.directory) {
    		var path = this.directory.path;
    		var length = path.length;
    		var tooltip_length = this.nodeOptions.tooltip_length || 50;
    		if(length > tooltip_length) {
    			path = ".." + path.substring(length-(tooltip_length-2), length);
    		}
    		this.$el.tooltip({
            	title: path,
            	placement: 'bottom'
            }); 
    	}
    },
    _search: function (search_val) {
    	var self = this;
    	return this._super.apply(this, arguments).then(function(results) {
    		if (results.length > self.limit) {
    			results.splice(results.length - 2, 0, {
                    label: _t("Open Finder..."),
                    action: self._openFinder.bind(self),
                    classname: 'o_m2o_dropdown_option',
                });
    		}
    		return results;
    	});
    },
    _openFinder: function() {
    	var self = this;
        return new DocumentDirectorySelectionDialog(this, _.extend({}, this.nodeOptions, {
        	title: _t("Find: ") + this.string,
        	on_selected: function (node) {
                self.reinitialize({id: node.data.odoo_id, display_name: node.data.name});
                self.activate();
            }
        })).open();
    },
});

registry.add('dms_directory', FieldDirectoryMany2One);

return FieldDirectoryMany2One;

});
