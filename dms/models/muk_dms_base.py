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

from openerp import _
from openerp import models, api, fields
from openerp.exceptions import ValidationError, AccessError

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
         _logger.debug("Change: " + str(change))
         
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
        _logger.info("Creating record ([" + self._name + "]) with values: " + self.__print_values(vals))
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
            _logger.info("Writing record ([" + record._name + "] - id: " + 
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

    The DMSBaseModel itself inherits the BaseModel class from OpenERP
    so every model which inherits it can be used as a normal
    OpenERP model.
    """
        
    _auto = True
    _register = False
    _transient = False

class DMSAbstractModel(DMSBaseModel):
    """Main super-class for file models.

    DMS file models are created by inheriting from this class:

        class class_name(DMSFileModel):

    The DMSFileModel itself inherits the BaseModel class from OpenERP
    so every model which inherits it can be used as a normal
    OpenERP model.
    """
    
    _auto = False 
    _register = False 
    _transient = False
    