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

odoo.define('muk_dms_widgets.size', function(require) {
"use strict";

var core = require('web.core');
var registry = require('web.field_registry');
var field_utils = require('web.field_utils');
var field_widgets = require('web.basic_fields');

var _t = core._t;
var QWeb = core.qweb;

function format_size(bytes, field, options) {
    var thresh = options.si ? 1000 : 1024;
    if(Math.abs(bytes) < thresh) {
        return field_utils.format['float'](bytes, field, options) + ' B';
    }
    var units = options.si
        ? ['KB','MB','GB','TB','PB','EB','ZB','YB']
        : ['KiB','MiB','GiB','TiB','PiB','EiB','ZiB','YiB'];
    var u = -1;
    do {
        bytes /= thresh;
        ++u;
    } while(Math.abs(bytes) >= thresh && u < units.length - 1);
    return field_utils.format['float'](bytes, field, options) + ' ' + units[u];
}

var FieldDocumentSize = field_widgets.FieldFloat.extend({
	 _renderReadonly: function () {
	    this.$el.text(format_size(this.value, this.field, this.nodeOptions));
    },
});

registry.add('dms_size', FieldDocumentSize);

return FieldDocumentSize;

});
