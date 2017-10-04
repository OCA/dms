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

var _t = core._t;
var QWeb = core.qweb;

var FieldDirectoryMany2One = field_widgets.FieldMany2One.extend({
	willStart: function () {
		var self = this;
		return $.when(this._super.apply(this, arguments)).then(function() {
			if(self.value) {
				return self._rpc({
	                fields: ['name', 'path', 'perm_read'],
	                domain: [['id', '=', self.value.data.id]],
	                model: 'muk_dms.directory',
	                method: 'search_read',
	                limit: 1,
	                context: session.user_context,
	            }).then(function(directories) {
	            	self.directory = directories.length > 0 ? directories[0] : null;
	            	self.nodeOptions.no_open = self.directory ? !self.directory.perm_read : true;
	            });
			}
        });
    },
	_renderEdit: function () {
        this._super.apply(this, arguments);
    	this._renderTooltip();
    },
    _renderReadonly: function () {
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
        var def = $.Deferred();
        this.orderer.add(def);
        var context = this.record.getContext(this.recordParams);
        var domain = this.record.getDomain(this.recordParams);
        var blacklisted_ids = this._getSearchBlacklist();
        if(blacklisted_ids.length > 0) {
            domain.push(['id', 'not in', blacklisted_ids]);
        }
        if(search_val.indexOf("/") !== -1) {
        	domain.push(['path', 'ilike', search_val]);
        } else {
        	domain.push(['name', 'ilike', search_val]);
        }
        this._rpc({
            fields: ['name', 'path', 'perm_create'],
            domain: domain,
            model: 'muk_dms.directory',
            method: 'search_read',
            limit: this.limit,
            context: context,
        }).then(function (directories) {
        	directories = _.filter(directories, function(directory, index) {
        		return directory.perm_create;
    		})
        	var values = _.map(directories, function (directory) {
        		var path = directory.path;
        		var length = directory.path.length;
        		var dropdown_length = self.nodeOptions.dropdown_length || 30;
        		if(length > dropdown_length) {
        			path = ".." + path.substring(length-(dropdown_length-2), length);
        		}
        		var name = self._getDisplayName(directory.name) + " (" + path + ")";
                return {
                    label: _.str.escapeHTML(name.trim()) || data.noDisplayContent,
                    value: name,
                    name: name,
                    id: directory.id,
                };
            });
            values.push({
                label: _t("Search More..."),
                action: function () {
                    self._rpc({
                            model: self.field.relation,
                            method: 'name_search',
                            kwargs: {
                                name: search_val,
                                args: domain,
                                operator: "ilike",
                                limit: 160,
                                context: context,
                            },
                        })
                        .then(self._searchCreatePopup.bind(self, "search"));
                },
                classname: 'o_m2o_dropdown_option',
            });
        	var create_enabled = self.can_create && !self.nodeOptions.no_create;
            var raw_result = _.map(directories, function (directory) { return directory.name; });
            if (create_enabled && self.quick_create &&
                search_val.length > 0 && !_.contains(raw_result, search_val)) {
                values.push({
                    label: _.str.sprintf(_t('Create "<strong>%s</strong>"'),
                        $('<span />').text(search_val).html()),
                    action: self._quickCreate.bind(self, search_val),
                    classname: 'o_m2o_dropdown_option'
                });
            }
            if (create_enabled && !self.nodeOptions.no_create_edit) {
                var createAndEditAction = function () {
                    self.$('input').val('');
                    return self._searchCreatePopup("form", false, self._createContext(search_val));
                };
                values.push({
                    label: _t("Create and Edit..."),
                    action: createAndEditAction,
                    classname: 'o_m2o_dropdown_option',
                });
            } else if (values.length === 0) {
                values.push({
                    label: _t("No results to show..."),
                });
            }
        	def.resolve(values);
        });
        return def;
    },
});

registry.add('dms_directory', FieldDirectoryMany2One);

return FieldDirectoryMany2One;

});
