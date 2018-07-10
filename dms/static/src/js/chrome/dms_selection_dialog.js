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

odoo.define('muk_dms_dialogs.DocumentSelectionDialog', function(require) {
"use strict";

var core = require('web.core');

var Dialog = require('web.Dialog');

var _t = core._t;
var QWeb = core.qweb;

var DocumentSelectionDialog = Dialog.extend({
    init: function (parent, options) {
    	var self = this;
    	this.options = options || {};
        var buttons = [
            {
            	text: _t("Select"),
            	classes: "btn-primary",
            	close: true, 
            	click: function () {
            		if(self.view) {
            			if(self.options.view.options.disable_multiple) {
            				self.on_selected(self.view.controller.getSelectedItem());
            			} else {
            				self.on_selected(self.view.controller.getSelectedItems());
            			}
            		}
            	}
            },
            {
            	text: _t("Close"),
            	close: true
            },
        ];
        this._super(parent, _.extend({}, {
            buttons: buttons,
        }, this.options));
        this.on_selected = this.options.on_selected || (function () {});
        if(this.options.view) {
        	var dialog_view = this.options.view;
        	this.view = new dialog_view.view(this, dialog_view.options);
        }
    },
    renderElement: function() {
        this._super();
        if(this.view) {
        	this.view.appendTo(this.$el);
        }
	},
});

return DocumentSelectionDialog;

});