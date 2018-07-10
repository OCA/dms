###################################################################################
# 
#    Copyright (C) 2017 MuK IT GmbH
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###################################################################################

import logging

from odoo import models, api, fields

_logger = logging.getLogger(__name__)

class Category(models.Model):
    
    _name = 'muk_dms.category'
    _description = "MuK Document Category"

    _rec_name = 'complete_name'
    
    _parent_store = True
    _parent_name = "parent_category"
    _parent_order = 'parent_left'
    _order = 'parent_left'
    
    #----------------------------------------------------------
    # Database
    #----------------------------------------------------------
    
    name = fields.Char(
        string='Name', 
        required=True, 
        translate=True)
    
    complete_name = fields.Char(
        string='Complete Name', 
        compute='_compute_complete_name',
        store=True)
    
    parent_category = fields.Many2one(
        comodel_name='muk_dms.category', 
        string='Parent Category',
        index=True, 
        ondelete='cascade')
    
    child_categories = fields.One2many(
        comodel_name='muk_dms.category', 
        inverse_name='parent_category',
        string='Child Categories')
    
    parent_left = fields.Integer(
        'Left Parent', 
        index=True)
    
    parent_right = fields.Integer(
        'Right Parent', 
        index=True)
    
    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Category name already exists!"),
    ]
       
    #----------------------------------------------------------
    # Read
    #----------------------------------------------------------

    @api.depends('name', 'parent_category.complete_name')
    def _compute_complete_name(self):
        for record in self:
            if record.parent_category:
                record.complete_name = '%s / %s' % (record.parent_category.complete_name, record.name)
            else:
                record.complete_name = record.name

    @api.constrains('parent_category')
    def _check_category_recursion(self):
        if not self._check_recursion():
            raise ValidationError(_('Error ! You cannot create recursive categories.'))
        return True

    @api.model
    def name_create(self, name):
        return self.create({'name': name}).name_get()[0]
