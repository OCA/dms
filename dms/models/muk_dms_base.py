# -*- coding: utf-8 -*-

###################################################################################
# 
#    MuK Document Management System
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

import os
import string
import unicodedata
import hashlib
import logging

from odoo import _
from odoo import models, api, fields
from odoo.exceptions import ValidationError, AccessError, UserError

_logger = logging.getLogger(__name__)

VALID_NAME_CHARS = "-_.() %s%s" % (string.letters, string.digits)

"""Changes"""
PATH = 'path_change'
ROOT = 'root_change'

class DMSBaseModel(models.BaseModel):
    """Main super-class for file models.
    
    The DMSBaseModel itself inherits the BaseModel class from OpenERP
    so every model which inherits it can be used as a normal
    OpenERP model.
    """
    
    _auto = False
    _register = False 
    _transient = False
    
    #----------------------------------------------------------
    # Function
    #----------------------------------------------------------

    def check_existence(self):
        return not (len(self) == 0 or self.id == False)
    
    def notify_change(self, change, values):
         _logger.debug("Notify Change: " + str(change))
    
    def notify_computation(self):
         _logger.debug("Notify Computation")
         
    def check_name(self, name):
        return set(VALID_NAME_CHARS).issuperset(name)
         
    def __print_values(self, values):
        print_vals = {}
        for key, value in values.iteritems():
            print_vals[key] = str(value)[:75] + (str(value)[75:] and '..')
        return str(print_vals)
    
    #----------------------------------------------------------
    # Read
    #----------------------------------------------------------
    
    @api.v8
    def read(self, fields=None, load='_classic_read'):
        self._before_read(fields)
        result = super(DMSBaseModel, self).read(fields, load)
        for index, record in enumerate(self):
            _logger.debug("Reading values for record ([" + record._name + "] - id: " + 
                          str(record.id) + ") - fields: " + str(fields)[:150] + (str(fields)[150:] and '..'))
            record._append_field_values(index, result)
        result = self._after_read(result)
        return result
        
    @api.v7
    def read(self, cr, user, ids, fields=None, context=None, load='_classic_read'):
        records = self.browse(cr, user, ids, context)
        result = DMSBaseModel.read(records, fields, load=load)
        return result if isinstance(ids, list) else (bool(result) and result[0])

    def _before_read(self, fields):
        pass

    def _append_field_values(self, index, result):
        return result

    def _after_read(self, result):
        return result
    
    @api.model
    @api.returns('self',
        upgrade=lambda self, value, args, offset=0, limit=None, order=None, count=False: value if count else self.browse(value),
        downgrade=lambda self, value, args, offset=0, limit=None, order=None, count=False: value if count else value.ids)
    def search(self, args, offset=0, limit=None, order=None, count=False):
        self._before_search(args, offset, limit, order, count)
        result = super(DMSBaseModel, self).search(args, offset, limit, order, count)
        _logger.debug("Searching for records  with ([" + str(args) + "])")
        result = self._after_search(result)
        return result
    
    def _before_search(self, args, offset, limit, order, count):
        pass

    def _after_search(self, result):
        return result
    
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        self._before_name_search(name, args, operator, limit)
        result = super(DMSBaseModel, self).name_search(name, args, operator, limit)
        _logger.debug("Searching for records  with ([" + str(args) + "])")
        result = self._after_name_search(result)
        return result
    
    def _before_name_search(self, name, args, operator, limit):
        pass

    def _after_name_search(self, result):
        return result
    
    #----------------------------------------------------------
    # Locking
    #----------------------------------------------------------

    @api.multi
    def lock(self, user=None):
        result = []
        for record in self:
            _logger.info("Locking record ([" + record._name + "] - id: " + 
                          str(record.id) + ")")
            token = hashlib.sha1(os.urandom(128)).hexdigest()
            lock = self.env['muk_dms.lock'].sudo().create({'locked_by': user and user.name or "System",
                                                           'locked_by_ref': user and user._name + ',' + str(user.id) or None,
                                                           'lock_ref': record._name + ',' + str(record.id),
                                                           'token': token})
            result.append({'record': record, 'lock': lock, 'token': token})
        return result
    
    @api.multi
    def unlock(self):
        for record in self:
            _logger.info("Unlocking record ([" + record._name + "] - id: " + 
                          str(record.id) + ")")
            locks = self.env['muk_dms.lock'].sudo().search([('lock_ref', '=', record._name + ',' + str(record.id))])
            for lock in locks: 
                lock.sudo().unlink()
        return True
    
    @api.multi
    def is_locked(self):
        self.ensure_one()
        lock = self.env['muk_dms.lock'].sudo().search([('lock_ref', '=', self._name + ',' + str(self.id))], limit=1)
        if lock.id:
            return lock
        return False
    
    @api.multi
    def is_locked_by(self):
        self.ensure_one()
        lock = self.env['muk_dms.lock'].sudo().search([('lock_ref', '=', self._name + ',' + str(self.id))], limit=1)
        if lock.id:
            return lock.locked_by_ref
        return False
    
    def _checking_lock(self):
        if self.is_locked():
            raise AccessError(_("The record is locked, so it can't be changes or deleted."))
    
    #----------------------------------------------------------
    # Create, Update, Delete
    #----------------------------------------------------------
    
    def _validate_values(self, values):
        pass
    
    @api.model
    def create(self, vals):
        vals = self._before_create(vals)
        _logger.debug("Creating record ([" + self._name + "]) with values: " + self.__print_values(vals))
        self._validate_values(vals)
        vals = self._append_values_create(vals)
        result = super(DMSBaseModel, self).create(vals)
        result = self._after_create(result, vals)
        return result
    
    def _before_create(self, vals):
        return vals
    
    def _append_values_create(self, values):
        return values
        
    def _after_create(self, result, vals):
        return result

    @api.multi
    def write(self, vals):
        vals = self._before_write(vals)
        for record in self:
            _logger.debug("Writing record ([" + record._name + "] - id: " + 
                          str(record.id) + ") with values: " + self.__print_values(vals))
            record._checking_lock()
            record._validate_values(vals)
            record._onchange_values(vals)
            vals = record._append_values_wirte(vals)
        result = super(DMSBaseModel, self).write(vals)
        for record in self:
            self._follow_operation(vals)
        result = self._after_write(result, vals)
        return result
    
    def _before_write(self, vals):
        return vals
    
    def _onchange_values(self, values):
        pass
    
    def _append_values_wirte(self, values):
        return values    
    
    def _follow_operation(self, values):
        pass
        
    def _after_write(self, result, vals):
        return result

    @api.multi
    def unlink(self):     
        self._before_unlink()
        for record in self:
            _logger.info("Unlinking record ([" + record._name + "] - id: " + 
                          str(record.id) + ")")
            record._checking_lock()
            record._check_unlink() 
            record.prepare_unlink() 
        result = super(DMSBaseModel, self).unlink()
        self._after_unlink()
        return result
    
    def _before_unlink(self):
        pass
    
    def _check_unlink(self):
        pass
        
    def prepare_unlink(self):
        pass
        
    def _after_unlink(self):
        pass

class DMSModel(DMSBaseModel):
    """Main super-class for regular database-persisted DMS models.

    DMS models are created by inheriting from this class:

        class class_name(DMSModel):

    The DMSBaseModel itself inherits the BaseModel class from Odoo
    so every model which inherits it can be used as a normal
    Odoo model.
    """
      
    _auto = True
    _register = False
    _transient = False
    
    
class DMSAccessModel(DMSModel):
    _name = 'muk_dms.access'
            
    perm_create = fields.Boolean(compute='_compute_perm_create', string="Create")
    perm_read = fields.Boolean(compute='_compute_perm_read', string="Read")
    perm_write = fields.Boolean(compute='_compute_perm_write', string="Write")
    perm_unlink = fields.Boolean(compute='_compute_perm_unlink', string="Delete")
    
    @api.model
    def check_access_rights(self, operation, raise_exception=True):
        """ Generic method giving the help message displayed when having
            no result to display in a list or kanban view. By default it returns
            the help given in parameter that is generally the help message
            defined in the action.
        """
        return super(DMSAccessModel, self).check_access_rights(operation, raise_exception)
    
    @api.multi
    def check_access_rule(self, operation):
        """ Verifies that the operation given by ``operation`` is allowed for
            the current user according to ir.rules.

           :param operation: one of ``write``, ``unlink``
           :raise UserError: * if current ir.rules do not permit this operation.
           :return: None if the operation is allowed
        """
        return super(DMSAccessModel, self).check_access_rule(operation)
    
    @api.model
    def _apply_ir_rules(self, query, mode='read'):
        super(DMSAccessModel, self)._apply_ir_rules(query, mode)
    
    @api.model
    def check_field_access_rights(self, operation, fields):
        """ Check the user access rights on the given fields. This raises Access
            Denied if the user does not have the rights. Otherwise it returns the
            fields (as is if the fields is not false, or the readable/writable
            fields if fields is false).
        """
        return super(DMSAccessModel, self).check_field_access_rights(operation, fields)
        
    @api.one
    def _compute_perm_create(self):
        try:
            self.perm_create = self.check_access_rights('create', raise_exception=False) and self.check_access_rule(operation='create') == None
        except AccessError:
             self.perm_create = False
            
    @api.one
    def _compute_perm_read(self):
        try:
            self.perm_read = self.check_access_rights('read', raise_exception=False) and self.check_access_rule(operation='read') == None
        except AccessError:
             self.perm_create = False
    
    @api.one
    def _compute_perm_write(self):
        try:
            self.perm_write = self.check_access_rights('write', raise_exception=False) and self.check_access_rule(operation='write') == None
        except AccessError:
             self.perm_create = False
        
    @api.one
    def _compute_perm_unlink(self):
        try:
            self.perm_unlink = self.check_access_rights('unlink', raise_exception=False) and self.check_access_rule(operation='unlink') == None
        except AccessError:
             self.perm_create = False
