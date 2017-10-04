# -*- coding: utf-8 -*-

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

import os
import time
import string
import shutil
import hashlib
import logging
import tempfile
import unicodedata

from odoo import _
from odoo import models, api, fields
from odoo.exceptions import ValidationError, AccessError, UserError

_logger = logging.getLogger(__name__)

# Refresh timeout, to prevent multiple refresh events triggering at once
TIMEOUT = 30

def timeout(func):
    def wrapper(*args, **kwargs):
        if args[0]._name in wrapper.timeouts:
            timeout = wrapper.timeouts[args[0]._name]
            if time.time() > timeout + TIMEOUT:
                wrapper.timeouts[args[0]._name] = time.time()
                return func(*args, **kwargs)
        else:
            wrapper.timeouts[args[0]._name] = time.time()
            return func(*args, **kwargs)
    wrapper.timeouts = {}
    return wrapper

class DMSBaseModel(models.BaseModel):
    """Main super-class for file models.
    
    The DMSBaseModel itself inherits the BaseModel class from Odoo
    so every model which inherits it can be used as a normal
    Odoo model.
    """
    
    _auto = False         
    _register = False   
    _abstract = True        
    _transient = False      

    _name = None     
    _description = None
    
    #----------------------------------------------------------
    # Function
    #----------------------------------------------------------

    def check_existence(self):
        records = self.exists()
        if not (len(records) == 0 or (len(records) == 1 and records.id == False)):
            return records
        else:
            return False
    
    def notify_change(self, values, refresh=False, operation=None):
        self.ensure_one()
        if refresh:
            self.refresh()
    
    def trigger_computation(self, fields, refresh=True, operation=None):
        self.ensure_one()
        if refresh:
            self.refresh()
         
    def check_name(self, name):
        tmp_dir = tempfile.mkdtemp()
        try:
            open(os.path.join(tmp_dir, name), 'a').close()
        except IOError:
            return False
        finally:
            shutil.rmtree(tmp_dir)
        return True
    
    @timeout
    def refresh(self):
        self.env['bus.bus'].sendone("refresh", [self.env.cr.dbname, self._name, self._uid])
    
    def generate_key(self):
        return hashlib.sha1(os.urandom(128)).hexdigest()
    
    def unique_name(self, name, names, escape_suffix=False):
        def compute_name(name, suffix, escape_suffix):
            if escape_suffix:
                name, extension = os.path.splitext(name)
                return "%s(%s)%s" % (name, suffix, extension)
            else:
                return "%s(%s)" % (name, suffix)
        if not name in names:
            return name
        else:
            suffix = 1
            name = compute_name(name, suffix, escape_suffix)
            while name in names:
                suffix += 1
                name = compute_name(name, suffix, escape_suffix)
            return name
    
    #----------------------------------------------------------
    # Read
    #----------------------------------------------------------
    
    def browse(self, arg=None, prefetch=None):
        arg = self._before_browse(arg)
        result = super(DMSBaseModel, self).browse(arg, prefetch)
        result = self._after_browse(result)
        return result
    
    def _before_browse(self, arg):
        return arg

    def _after_browse(self, result):
        return result
    
    @api.multi
    def read(self, fields=None, load='_classic_read'):
        fields = self._before_read(fields)
        result = super(DMSBaseModel, self).read(fields, load)
        for index, record in enumerate(self.exists()):
            result[index] = record._after_read_record(result[index])
        result = self._after_read(result)
        return result

    def _before_read(self, fields):
        return fields

    def _after_read_record(self, values):
        return values

    def _after_read(self, result):
        return result
    
    @api.model
    @api.returns('self',
        upgrade=lambda self, value, args, offset=0, limit=None, order=None, count=False: value if count else self.browse(value),
        downgrade=lambda self, value, args, offset=0, limit=None, order=None, count=False: value if count else value.ids)
    def search(self, args, offset=0, limit=None, order=None, count=False):
        args, offset, limit, order, count = self._before_search(args, offset, limit, order, count)
        result = super(DMSBaseModel, self).search(args, offset, limit, order, count)
        result = self._after_search(result)
        return result
    
    def _before_search(self, args, offset, limit, order, count):
        return args, offset, limit, order, count
    
    def _after_search(self, result):
        return result
    
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        name, args, operator, limit = self._before_name_search(name, args, operator, limit)
        result = super(DMSBaseModel, self).name_search(name, args, operator, limit)
        result = self._after_name_search(result)
        return result
    
    def _before_name_search(self, name, args, operator, limit):
        return name, args, operator, limit

    def _after_name_search(self, result):
        return result
    
    #----------------------------------------------------------
    # Locking
    #----------------------------------------------------------

    @api.multi
    def lock(self, user=None, refresh=False, operation=None):
        result = []
        for record in self:
            lock = record.is_locked()
            if lock and lock.operation and lock.operation == operation:
                result.append({
                    'record': record, 
                    'lock': lock, 
                    'token': lock.token})
            elif lock and ((lock.operation and lock.operation != operation) or not lock.operation):
                raise AccessError(_("The record (%s[%s]) is locked, so it can't be locked again.") %
                                   (record._name, record.id))
            else:
                token = hashlib.sha1(os.urandom(128)).hexdigest()
                lock = self.env['muk_dms.lock'].sudo().create({
                    'locked_by': user and user.name or "System",
                    'locked_by_ref': user and user._name + ',' + str(user.id) or None,
                    'lock_ref': record._name + ',' + str(record.id),
                    'token': token,
                    'operation': operation})
                result.append({
                    'record': record, 
                    'lock': lock, 
                    'token': token})
        if refresh:
            self.refresh()
        return result
    
    @api.multi
    def unlock(self, refresh=False):
        for record in self:
            locks = self.env['muk_dms.lock'].sudo().search([('lock_ref', '=', record._name + ',' + str(record.id))])
            for lock in locks: 
                lock.sudo().unlink()
        if refresh:
            self.refresh()
        return True
    
    @api.model
    def unlock_operation(self, operation, refresh=False):
        locks = self.env['muk_dms.lock'].sudo().search([('operation', '=', operation)])
        for lock in locks: 
            lock.sudo().unlink()
        if refresh:
            self.refresh()
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
    
    def _checking_lock(self, operation=None):
        self._checking_lock_user()
        for record in self:
            lock = record.is_locked()
            if lock and lock.operation and lock.operation != operation:
                raise AccessError(_("The record (%s[%s]) is locked, so it can't be changes or deleted.") %
                                   (self._name, self.id))
            
    def _checking_lock_user(self):
        for record in self:
            lock = record.is_locked()
            if lock and lock.locked_by_ref and not lock.locked_by_ref != self.env.user:
                raise AccessError(_("The record (%s[%s]) is locked by a user, so it can't be changes or deleted.") %
                                   (self._name, self.id))
    
    def user_lock(self):
        self.ensure_one()
        lock = self.is_locked()
        if lock:
            if lock.locked_by_ref:
                raise AccessError(_("The record is already locked by another user. (%s)") % lock.locked_by_ref.name)
            else:
                raise AccessError(_("The record is already locked."))
        return self.lock(user=self.env.user, refresh=True)
    
    def user_unlock(self):
        self.ensure_one()
        lock = self.is_locked()
        if lock:
            if lock.locked_by_ref and lock.locked_by_ref.id == self.env.user.id:
                self.unlock(refresh=True)
            else:
                if lock.locked_by_ref:
                    raise AccessError(_("The record is already locked by another user. (%s)") % lock.locked_by_ref.name)
                else:
                    raise AccessError(_("The record is already locked."))
     
    #----------------------------------------------------------
    # Create, Update, Delete
    #----------------------------------------------------------
    
    @api.model
    def create(self, vals):
        vals = self._before_create(vals)
        self.check_access_rights('create')
        result = super(DMSBaseModel, self.sudo()).create(vals)
        result = result._after_create(vals)
        return result
    
    def _before_create(self, vals):
        return vals
        
    def _after_create(self, vals):
        return self

    @api.multi
    def write(self, vals):
        operation = self.generate_key()
        vals = self._before_write(vals, operation)
        result = super(DMSBaseModel, self).write(vals)
        for record in self:
            record._after_write_record(vals, operation)
        result = self._after_write(result, vals, operation)
        return result
    
    def _before_write(self, vals, operation):
        if 'operation' in self.env.context:
            self._checking_lock(self.env.context['operation'])
        elif operation:
            self._checking_lock(operation)
        else:
            self._checking_lock_user()
        return vals
    
    def _after_write_record(self, vals, operation):
        return vals    
        
    def _after_write(self, result, vals, operation):
        return result

    @api.multi
    def unlink(self):  
        operation = self.generate_key()
        info = self._before_unlink(operation)
        infos = []
        for record in self:
            infos.append(record._before_unlink_record(operation))
        result = super(DMSBaseModel, self).unlink()
        self._after_unlink(result, info, infos, operation)
        return result
    
    def _before_unlink(self, operation):
        if 'operation' in self.env.context:
            self._checking_lock(self.env.context['operation'])
        elif operation:
            self._checking_lock(operation)
        else:
            self._checking_lock_user()
        return {}
    
    def _before_unlink_record(self, operation):
        return {}    
        
    def _after_unlink(self, result, info, infos, operation):
        pass

DMSAbstractModel = DMSBaseModel

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
    _abstract = False
    
class DMSAccessModel(DMSAbstractModel):
    _name = 'muk_dms.access'
    _description = "MuK Documents Access"
    
    #----------------------------------------------------------
    # Database
    #----------------------------------------------------------
            
    perm_create = fields.Boolean(
        compute='_compute_perm_create',
        string="Create")
    
    perm_read = fields.Boolean(
        compute='_compute_perm_read',
        string="Read")
    
    perm_write = fields.Boolean(
        compute='_compute_perm_write',
        string="Write")
    
    perm_unlink = fields.Boolean(
        compute='_compute_perm_unlink', 
        string="Delete")
        
    locked = fields.Many2one(
        'muk_dms.lock', 
        compute='_compute_lock', 
        string="Locked", 
        prefetch=False)
    
    editor = fields.Boolean(
        compute='_compute_editor', 
        string="Editor", 
        prefetch=False)
        
    #----------------------------------------------------------
    # Function
    #----------------------------------------------------------
    
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
    
    def check_access(self, operation, raise_exception=False):
        try:
            access_right = self.check_access_rights(operation, raise_exception)
            access_rule = self.check_access_rule(operation) == None
            return access_right and access_rule
        except AccessError:
            if raise_exception:
                raise AccessError(_("This operation is forbidden!"))
            return False
        
    #----------------------------------------------------------
    # Read, View 
    #----------------------------------------------------------
        
    @api.one
    def _compute_perm_read(self):
        try:
            self.perm_read = self.check_access('read')
        except AccessError:
             self.perm_read = False
        
    @api.one
    def _compute_perm_create(self):
        try:
            self.perm_create = self.check_access('create')
        except AccessError:
             self.perm_create = False
    
    @api.one
    def _compute_perm_write(self):
        try:
            self.perm_write = self.check_access('write')
        except AccessError:
             self.perm_write = False
        
    @api.one
    def _compute_perm_unlink(self):
        try:
            self.perm_unlink = self.check_access('unlink')
        except AccessError:
             self.perm_unlink = False
             
    @api.one
    def _compute_lock(self):
        self.locked = self.is_locked()
      
    @api.one  
    def _compute_editor(self):
        self.editor = self.is_locked_by() == self.env.user
    
    #----------------------------------------------------------
    # Create, Update, Delete
    #----------------------------------------------------------
    
    def _before_create(self, vals):
        self.check_access('create', raise_exception=True)
        return super(DMSAccessModel, self)._before_create(vals)
        
    def _before_write(self, vals, operation):
        for record in self:
            record.check_access('write', raise_exception=True)
        return super(DMSAccessModel, self)._before_write(vals, operation)
    
    def _before_unlink(self, operation):
        for record in self:
            record.check_access('unlink', raise_exception=True)
        return super(DMSAccessModel, self)._before_unlink(operation)