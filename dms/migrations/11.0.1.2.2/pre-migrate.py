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

_sql_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'sql'))

def migrate(cr, version):
    if not version:
        return
    
    if version == "10.0.1.1.0":
        sql_pre_migration_files = [
            os.path.join(_sql_path, "100110/pre_delete_locks.sql"),
            os.path.join(_sql_path, "100110/pre_muk_dms_data_database.sql"),
            os.path.join(_sql_path, "100110/pre_muk_dms_directory.sql"),
            os.path.join(_sql_path, "100110/pre_muk_dms_file.sql"),
            os.path.join(_sql_path, "100110/pre_muk_dms_settings.sql"),
            os.path.join(_sql_path, "100110/pre_fkey_for_muk_dms_settings.sql"),
            os.path.join(_sql_path, "100110/pre_muk_dms_lock.sql"),
            os.path.join(_sql_path, "100110/pre_drop_old_tables.sql")]
        for sql_file in sql_pre_migration_files:
            with open(sql_file,'r') as file:
                input = file.readlines()
            input = [x.strip() for x in input] 
            for sql_query in input:
                if sql_query and not sql_query.startswith("--"):
                    cr.execute(sql_query)
                    
    if version == "11.0.1.2.2":
        sql_pre_migration_files = [
            os.path.join(_sql_path, "110122/pre_fkey_for_muk_dms_settings.sql")]
        for sql_file in sql_pre_migration_files:
            with open(sql_file,'r') as file:
                input = file.readlines()
            input = [x.strip() for x in input] 
            for sql_query in input:
                if sql_query and not sql_query.startswith("--"):
                    cr.execute(sql_query)