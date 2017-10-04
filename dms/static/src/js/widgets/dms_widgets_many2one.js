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

odoo.define('muk_dms_widgets.many2one', function(require) {
"use strict";

var core = require('web.core');
var registry = require('web.field_registry');
var field_utils = require('web.field_utils');
var field_widgets = require('web.relational_fields');

var PreviewHelper = require('muk_dms_preview_file.PreviewHelper');

var _t = core._t;
var QWeb = core.qweb;

var FieldDocumentMany2One = field_widgets.FieldMany2One.extend({
    template: 'FieldDocumentMany2One',
    _renderReadonly: function () {
    	var self = this;
        var value = _.escape((this.m2o_value || "").trim()).split("\n").join("<br/>");
        if (!this.nodeOptions.no_open) {
            this.$el.find('.o_form_uri').html(value);
    		this.$el.find('.muk_form_document_preview').click(function (e) {
                e.preventDefault();
                e.stopPropagation();
                PreviewHelper.createFilePreviewDialog(self.value.data.id, self);
            });
        } else {
        	this._super.apply(this, arguments);
        }
    },
});

registry.add('dms_many2one', FieldDocumentMany2One);

return FieldDocumentMany2One;

});
