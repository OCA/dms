###################################################################################
#
#    Copyright (c) 2017-2019 MuK IT GmbH.
#
#    This file is part of MuK Documents 
#    (see https://mukit.at).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
###################################################################################

import os
import time
import logging
import unittest
import threading
import functools

from odoo import SUPERUSER_ID
from odoo.tests import common
from odoo.tests import tagged
from odoo.tools.profiler import profile
from odoo.tools import config, convert_file
from odoo.modules.module import get_resource_path
from odoo.modules.module import get_module_resource

from odoo.addons.muk_utils.tests.common import multi_users
from odoo.addons.muk_utils.tests.common import track_function

_path = os.path.dirname(os.path.dirname(__file__))
_logger = logging.getLogger(__name__)

@tagged('-standard', 'benchmark')
class BenchmarkTestCase(common.SavepointCase): 
    
    @classmethod
    def setUpClass(cls):
        super(BenchmarkTestCase, cls).setUpClass()
        cls._clean_existing_records()
        cls._setup_benchmark_data()
        
    @classmethod
    def _clean_existing_records(cls):
        cls.env['muk_dms.category'].search([]).unlink()
        cls.env['muk_dms.directory'].search([]).unlink()
        cls.env['muk_dms.storage'].search([]).unlink()
        cls.env['muk_dms.tag'].search([]).unlink()   
        
    @classmethod
    def _load(cls, module, *args):
        convert_file(cls.cr, 'muk_dms', get_module_resource(module, *args),
            {}, 'init', False, 'test', cls.registry._assertion_report)
  
    @classmethod  
    def _setup_benchmark_data(cls):
        cls._load('muk_dms', 'tests', 'data', 'muk_dms.category.csv')
        cls._load('muk_dms', 'tests', 'data', 'muk_dms.storage.csv')
        cls._load('muk_dms', 'tests', 'data', 'muk_dms.tag.csv')
        cls._load('muk_dms', 'tests', 'data', 'muk_dms.directory.csv')
        cls._load('muk_dms', 'tests', 'data', 'muk_dms.file.csv')

    def _benchmark_table(self, data):
        columns = len(data[0]) - 1
        format = "{:7}" + "| {:28}" * columns

        result = (format.format(*data[0]) + "\n")
        result += (("-" * 7) + (("+" + ("-") * 29) * columns) + "\n")
        for row in data[1:]:
            result += (format.format(*row) + "\n")
        return result
    
    def _benchmark_function(self, func, args_list):
        tfunc = track_function(return_tracking=True)(func)
        benchmark = []
        for item in args_list:
            self.registry.clear_caches()
            args = item[0] if len(item) > 0 else []
            kwargs = item[1] if len(item) > 1 else {}
            tracking = tuple(tfunc(*args, **kwargs)[1][1:])
            benchmark.append("%sq %.3fs %.3fs %.3fs" % tracking)
        return benchmark
    
    #----------------------------------------------------------
    # File
    #----------------------------------------------------------

    def _file_kanban_fields(self):
        return [
            'id', 'tags', 'name', 'color', 'active', 'mimetype', 'create_uid', 'write_date', 'locked_by',
            'is_locked', 'is_lock_editor', 'permission_write', 'permission_unlink', '__last_update'
        ]

    def test_file_search_benchmark(self):
        demo_uid = self.browse_ref("base.user_demo").id
        admin_uid = self.browse_ref("base.user_admin").id
        model =  self.env['muk_dms.file'].with_context(bin_size=True)
        args = [[[[]], {'limit': 1}], [[[]], {'limit': 80}], [[[]], {'limit': 500}], [[[]]]]
        
        benchmark_data_super = ['Super'] + self._benchmark_function(model.sudo().search, args)
        benchmark_data_admin = ['Admin'] + self._benchmark_function(model.sudo(admin_uid).search, args)
        benchmark_data_demo = ['Demo'] + self._benchmark_function(model.sudo(demo_uid).search, args)

        info_message = "\n\nSearching files with bin_size = True | "
        info_message += "Benchmark with Limit 1 / 80 / 500 / None (1500)\n\n"
        info_message += self._benchmark_table([
            ["User", "Search Limit 1", "Search Limit 80", "Search Limit 500", "Search No Limit"], 
            benchmark_data_super, benchmark_data_admin, benchmark_data_demo
        ])
        info_message += "\nLegend: Queries | Query Time | Server Time | Total Time\n"
        _logger.info(info_message)
        
    def test_file_search_read_benchmark(self):
        demo_uid = self.browse_ref("base.user_demo").id
        admin_uid = self.browse_ref("base.user_admin").id
        model =  self.env['muk_dms.file'].with_context(bin_size=True)
        args = [[[], {'limit': 1}], [[], {'limit': 80}], [[], {'limit': 500}], [[]]]
        
        benchmark_data_super = ['Super'] + self._benchmark_function(model.sudo().search_read, args)
        benchmark_data_admin = ['Admin'] + self._benchmark_function(model.sudo(admin_uid).search_read, args)
        benchmark_data_demo = ['Demo'] + self._benchmark_function(model.sudo(demo_uid).search_read, args)
        
        info_message = "\n\nSearching and reading all fields with bin_size = True | "
        info_message += "Benchmark with Limit 1 / 80 / 500 / None (1500)\n\n"
        info_message += self._benchmark_table([
            ["User", "Search Limit 1", "Search Limit 80", "Search Limit 500", "Search No Limit"], 
            benchmark_data_super, benchmark_data_admin, benchmark_data_demo
        ])
        info_message += "\nLegend: Queries | Query Time | Server Time | Total Time\n"
        _logger.info(info_message)
        
    def test_file_search_name_get_benchmark(self):
        demo_uid = self.browse_ref("base.user_demo").id
        admin_uid = self.browse_ref("base.user_admin").id
        model =  self.env['muk_dms.file'].with_context(bin_size=True)
        
        def test_function(model, limit):
            return model.search([], limit=limit).name_get()
        
        model_super = model.sudo()
        model_admin = model.sudo(admin_uid)
        model_demo = model.sudo(demo_uid)
        args_super = [[[model_super, 1]], [[model_super, 800]], [[model_super, 500]], [[model_super, None]]]
        args_admin = [[[model_admin, 1]], [[model_admin, 800]], [[model_admin, 500]], [[model_admin, None]]]
        args_demo = [[[model_demo, 1]], [[model_demo, 800]], [[model_demo, 500]], [[model_demo, None]]]
        
        benchmark_data_super = ['Super'] + self._benchmark_function(test_function, args_super)
        benchmark_data_admin = ['Admin'] + self._benchmark_function(test_function, args_admin)
        benchmark_data_demo = ['Demo'] + self._benchmark_function(test_function, args_demo)
        
        info_message = "\n\nSearching and 'name_get' function with bin_size = True | "
        info_message += "Benchmark with Limit 1 / 80 / 500 / None (1500)\n\n"
        info_message += self._benchmark_table([
            ["User", "Search Limit 1", "Search Limit 80", "Search Limit 500", "Search No Limit"], 
            benchmark_data_super, benchmark_data_admin, benchmark_data_demo
        ])
        info_message += "\nLegend: Queries | Query Time | Server Time | Total Time\n"
        _logger.info(info_message)
    
    def test_file_kanban_backend_benchmark(self):
        demo_uid = self.browse_ref("base.user_demo").id
        admin_uid = self.browse_ref("base.user_admin").id
        model =  self.env['muk_dms.file'].with_context(bin_size=True)
        kanban_fields = self._file_kanban_fields()
        
        def test_function(model, kanban_fields, limit=80):
            model.search_panel_select_range('directory')
            model.search_panel_select_multi_range('directory')
            model.search_panel_select_multi_range('tags')
            model.search_read(fields=kanban_fields, limit=limit)
        
        def function_args(args, kwargs):
            return [[args, {'limit': arg}] for arg in kwargs]
                
        args_super = function_args([model.sudo(), kanban_fields], [1, 80, 500, None])
        args_admin = function_args([model.sudo(admin_uid), kanban_fields], [1, 80, 500, None])
        args_demo = function_args([model.sudo(demo_uid), kanban_fields], [1, 80, 500, None])
        
        benchmark_data_super = ['Super'] + self._benchmark_function(test_function, args_super)
        benchmark_data_admin = ['Admin'] + self._benchmark_function(test_function, args_admin)
        benchmark_data_demo = ['Demo'] + self._benchmark_function(test_function, args_demo)
        
        info_message = "\n\nSimulate kanban view loading on the backend | "
        info_message += "Benchmark with Limit 1 / 80 / 500 / None (1500)\n\n"
        info_message += self._benchmark_table([
            ["User", "Search Limit 1", "Search Limit 80", "Search Limit 500", "Search No Limit"], 
            benchmark_data_super, benchmark_data_admin, benchmark_data_demo
        ])
        info_message += "\nLegend: Queries | Query Time | Server Time | Total Time || "
        info_message += "500 Directories | 150 Tags | 50 Categories\n"
        _logger.info(info_message)
    
    #----------------------------------------------------------
    # Directory
    #----------------------------------------------------------

    def test_directory_search_benchmark(self):
        demo_uid = self.browse_ref("base.user_demo").id
        admin_uid = self.browse_ref("base.user_admin").id
        model =  self.env['muk_dms.directory'].with_context(bin_size=True)
        args = [[[[]], {'limit': 1}], [[[]], {'limit': 80}], [[[]], {'limit': 500}], [[[]]]]
        
        benchmark_data_super = ['Super'] + self._benchmark_function(model.sudo().search, args)
        benchmark_data_admin = ['Admin'] + self._benchmark_function(model.sudo(admin_uid).search, args)
        benchmark_data_demo = ['Demo'] + self._benchmark_function(model.sudo(demo_uid).search, args)

        info_message = "\n\nSearching directories with bin_size = True | "
        info_message += "Benchmark with Limit 1 / 80 / 500 / None (1500)\n\n"
        info_message += self._benchmark_table([
            ["User", "Search Limit 1", "Search Limit 80", "Search Limit 500", "Search No Limit"], 
            benchmark_data_super, benchmark_data_admin, benchmark_data_demo
        ])
        info_message += "\nLegend: Queries | Query Time | Server Time | Total Time\n"
        _logger.info(info_message)
    
    def test_directory_search_parents_benchmark(self):
        demo_uid = self.browse_ref("base.user_demo").id
        admin_uid = self.browse_ref("base.user_admin").id
        model =  self.env['muk_dms.directory'].with_context(bin_size=True)
        args = [[[[]], {'limit': 1}], [[[]], {'limit': 80}], [[[]], {'limit': 500}], [[[]]]]
        
        benchmark_data_super = ['Super'] + self._benchmark_function(model.sudo().search_parents, args)
        benchmark_data_admin = ['Admin'] + self._benchmark_function(model.sudo(admin_uid).search_parents, args)
        benchmark_data_demo = ['Demo'] + self._benchmark_function(model.sudo(demo_uid).search_parents, args)

        info_message = "\n\nSearching directory parents with bin_size = True | "
        info_message += "Benchmark with Limit 1 / 80 / 500 / None (1500)\n\n"
        info_message += self._benchmark_table([
            ["User", "Search Limit 1", "Search Limit 80", "Search Limit 500", "Search No Limit"], 
            benchmark_data_super, benchmark_data_admin, benchmark_data_demo
        ])
        info_message += "\nLegend: Queries | Query Time | Server Time | Total Time\n"
        _logger.info(info_message)
        
    def test_directory_search_read_benchmark(self):
        demo_uid = self.browse_ref("base.user_demo").id
        admin_uid = self.browse_ref("base.user_admin").id
        model =  self.env['muk_dms.directory'].with_context(bin_size=True)
        args = [[[], {'limit': 1}], [[], {'limit': 80}], [[], {'limit': 500}], [[]]]
        
        benchmark_data_super = ['Super'] + self._benchmark_function(model.sudo().search_read, args)
        benchmark_data_admin = ['Admin'] + self._benchmark_function(model.sudo(admin_uid).search_read, args)
        benchmark_data_demo = ['Demo'] + self._benchmark_function(model.sudo(demo_uid).search_read, args)
        
        info_message = "\n\nSearching and reading all fields with bin_size = True | "
        info_message += "Benchmark with Limit 1 / 80 / 500 / None (1500)\n\n"
        info_message += self._benchmark_table([
            ["User", "Search Limit 1", "Search Limit 80", "Search Limit 500", "Search No Limit"], 
            benchmark_data_super, benchmark_data_admin, benchmark_data_demo
        ])
        info_message += "\nLegend: Queries | Query Time | Server Time | Total Time\n"
        _logger.info(info_message)
    
    #----------------------------------------------------------
    # Profiler
    #----------------------------------------------------------
    
    @unittest.skip("Takes to long to be tested every time.")
    def test_file_search_read_profile_admin(self):
        @track_function()
        @profile(minimum_queries=35)
        def profile_function(model):
            model.search_read([])
        admin_uid = self.browse_ref("base.user_admin").id
        model =  self.env['muk_dms.file'].sudo(admin_uid)
        profile_function(model.with_context(bin_size=True))
        
    