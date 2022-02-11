# Copyright 2017-2019 MuK IT GmbH.
# Copyright 2020 Creu Blanca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging
import unittest

from odoo.modules.module import get_module_resource
from odoo.tests import common, tagged
from odoo.tools import convert_file
from odoo.tools.misc import profile

from .common import track_function

_logger = logging.getLogger(__name__)


# This tests will only be executed if --test-tags benchmark is defined
@tagged("-standard", "benchmark")
class BenchmarkTestCase(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super(BenchmarkTestCase, cls).setUpClass()
        cls._clean_existing_records()
        cls._setup_benchmark_data()

    @classmethod
    def _clean_existing_records(cls):
        cls.env["dms.category"].search([]).unlink()
        cls.env["dms.directory"].search([]).unlink()
        cls.env["dms.storage"].search([]).unlink()
        cls.env["dms.tag"].search([]).unlink()

    @classmethod
    def _load(cls, module, *args):
        convert_file(
            cls.cr,
            "dms",
            get_module_resource(module, *args),
            {},
            "init",
            False,
            "test",
            cls.registry._assertion_report,
        )

    @classmethod
    def _setup_benchmark_data(cls):
        cls._load("dms", "tests", "data", "dms.category.csv")
        cls._load("dms", "tests", "data", "dms.storage.csv")
        cls._load("dms", "tests", "data", "dms.tag.csv")
        cls._load("dms", "tests", "data", "dms.directory.csv")
        cls._load("dms", "tests", "data", "dms.file.csv")

    def _benchmark_table(self, data):
        columns = len(data[0]) - 1
        formt = "{:7}" + "| {:28}" * columns

        result = formt.format(*data[0]) + "\n"
        result += ("-" * 7) + (("+" + ("-") * 29) * columns) + "\n"
        for row in data[1:]:
            result += formt.format(*row) + "\n"
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

    # ----------------------------------------------------------
    # File
    # ----------------------------------------------------------

    def _file_kanban_fields(self):
        return [
            "id",
            "tag_ids",
            "name",
            "color",
            "active",
            "mimetype",
            "create_uid",
            "write_date",
            "locked_by",
            "is_locked",
            "is_lock_editor",
            "permission_write",
            "permission_unlink",
            "__last_update",
        ]

    def test_file_search_benchmark(self):
        demo_uid = self.browse_ref("base.user_demo").id
        admin_uid = self.browse_ref("base.user_admin").id
        model = self.env["dms.file"].with_context(bin_size=True)
        args = [
            [[[]], {"limit": 1}],
            [[[]], {"limit": 80}],
            [[[]], {"limit": 500}],
            [[[]]],
        ]

        benchmark_data_super = ["Super"] + self._benchmark_function(
            model.sudo().search, args
        )
        benchmark_data_admin = ["Admin"] + self._benchmark_function(
            model.with_user(admin_uid).search, args
        )
        benchmark_data_demo = ["Demo"] + self._benchmark_function(
            model.with_user(demo_uid).search, args
        )

        info_message = "\n\nSearching files with bin_size = True | "
        info_message += "Benchmark with Limit 1 / 80 / 500 / None (1500)\n\n"
        info_message += self._benchmark_table(
            [
                [
                    "User",
                    "Search Limit 1",
                    "Search Limit 80",
                    "Search Limit 500",
                    "Search No Limit",
                ],
                benchmark_data_super,
                benchmark_data_admin,
                benchmark_data_demo,
            ]
        )
        info_message += "\nLegend: Queries | Query Time | Server Time | Total Time\n"
        _logger.info(info_message)

    def test_file_search_read_benchmark(self):
        demo_uid = self.browse_ref("base.user_demo").id
        admin_uid = self.browse_ref("base.user_admin").id
        model = self.env["dms.file"].with_context(bin_size=True)
        args = [[[], {"limit": 1}], [[], {"limit": 80}], [[], {"limit": 500}], [[]]]

        benchmark_data_super = ["Super"] + self._benchmark_function(
            model.sudo().search_read, args
        )
        benchmark_data_admin = ["Admin"] + self._benchmark_function(
            model.with_user(admin_uid).search_read, args
        )
        benchmark_data_demo = ["Demo"] + self._benchmark_function(
            model.with_user(demo_uid).search_read, args
        )

        info_message = "\n\nSearching and reading all fields with bin_size = True | "
        info_message += "Benchmark with Limit 1 / 80 / 500 / None (1500)\n\n"
        info_message += self._benchmark_table(
            [
                [
                    "User",
                    "Search Limit 1",
                    "Search Limit 80",
                    "Search Limit 500",
                    "Search No Limit",
                ],
                benchmark_data_super,
                benchmark_data_admin,
                benchmark_data_demo,
            ]
        )
        info_message += "\nLegend: Queries | Query Time | Server Time | Total Time\n"
        _logger.info(info_message)

    def test_file_search_name_get_benchmark(self):
        demo_uid = self.browse_ref("base.user_demo").id
        admin_uid = self.browse_ref("base.user_admin").id
        model = self.env["dms.file"].with_context(bin_size=True)

        def test_function(model, limit):
            return model.search([], limit=limit).name_get()

        model_super = model.sudo()
        model_admin = model.with_user(admin_uid)
        model_demo = model.with_user(demo_uid)
        args_super = [
            [[model_super, 1]],
            [[model_super, 800]],
            [[model_super, 500]],
            [[model_super, None]],
        ]
        args_admin = [
            [[model_admin, 1]],
            [[model_admin, 800]],
            [[model_admin, 500]],
            [[model_admin, None]],
        ]
        args_demo = [
            [[model_demo, 1]],
            [[model_demo, 800]],
            [[model_demo, 500]],
            [[model_demo, None]],
        ]

        benchmark_data_super = ["Super"] + self._benchmark_function(
            test_function, args_super
        )
        benchmark_data_admin = ["Admin"] + self._benchmark_function(
            test_function, args_admin
        )
        benchmark_data_demo = ["Demo"] + self._benchmark_function(
            test_function, args_demo
        )

        info_message = "\n\nSearching and 'name_get' function with bin_size = True | "
        info_message += "Benchmark with Limit 1 / 80 / 500 / None (1500)\n\n"
        info_message += self._benchmark_table(
            [
                [
                    "User",
                    "Search Limit 1",
                    "Search Limit 80",
                    "Search Limit 500",
                    "Search No Limit",
                ],
                benchmark_data_super,
                benchmark_data_admin,
                benchmark_data_demo,
            ]
        )
        info_message += "\nLegend: Queries | Query Time | Server Time | Total Time\n"
        _logger.info(info_message)

    def test_file_kanban_backend_benchmark(self):
        demo_uid = self.browse_ref("base.user_demo").id
        admin_uid = self.browse_ref("base.user_admin").id
        model = self.env["dms.file"].with_context(bin_size=True)
        kanban_fields = self._file_kanban_fields()

        def test_function(model, kanban_fields, limit=80):
            model.search_panel_select_range("directory_id")
            model.search_panel_select_multi_range("directory_id")
            model.search_panel_select_multi_range("tag_ids")
            model.search_read(fields=kanban_fields, limit=limit)

        def function_args(args, kwargs):
            return [[args, {"limit": arg}] for arg in kwargs]

        args_super = function_args([model.sudo(), kanban_fields], [1, 80, 500, None])
        args_admin = function_args(
            [model.with_user(admin_uid), kanban_fields], [1, 80, 500, None]
        )
        args_demo = function_args(
            [model.with_user(demo_uid), kanban_fields], [1, 80, 500, None]
        )

        benchmark_data_super = ["Super"] + self._benchmark_function(
            test_function, args_super
        )
        benchmark_data_admin = ["Admin"] + self._benchmark_function(
            test_function, args_admin
        )
        benchmark_data_demo = ["Demo"] + self._benchmark_function(
            test_function, args_demo
        )

        info_message = "\n\nSimulate kanban view loading on the backend | "
        info_message += "Benchmark with Limit 1 / 80 / 500 / None (1500)\n\n"
        info_message += self._benchmark_table(
            [
                [
                    "User",
                    "Search Limit 1",
                    "Search Limit 80",
                    "Search Limit 500",
                    "Search No Limit",
                ],
                benchmark_data_super,
                benchmark_data_admin,
                benchmark_data_demo,
            ]
        )
        info_message += "\nLegend: Queries | Query Time | Server Time | Total Time || "
        info_message += "500 Directories | 150 Tags | 50 Categories\n"
        _logger.info(info_message)

    # ----------------------------------------------------------
    # Directory
    # ----------------------------------------------------------

    def test_directory_search_benchmark(self):
        demo_uid = self.browse_ref("base.user_demo").id
        admin_uid = self.browse_ref("base.user_admin").id
        model = self.env["dms.directory"].with_context(bin_size=True)
        args = [
            [[[]], {"limit": 1}],
            [[[]], {"limit": 80}],
            [[[]], {"limit": 500}],
            [[[]]],
        ]

        benchmark_data_super = ["Super"] + self._benchmark_function(
            model.sudo().search, args
        )
        benchmark_data_admin = ["Admin"] + self._benchmark_function(
            model.with_user(admin_uid).search, args
        )
        benchmark_data_demo = ["Demo"] + self._benchmark_function(
            model.with_user(demo_uid).search, args
        )

        info_message = "\n\nSearching directories with bin_size = True | "
        info_message += "Benchmark with Limit 1 / 80 / 500 / None (1500)\n\n"
        info_message += self._benchmark_table(
            [
                [
                    "User",
                    "Search Limit 1",
                    "Search Limit 80",
                    "Search Limit 500",
                    "Search No Limit",
                ],
                benchmark_data_super,
                benchmark_data_admin,
                benchmark_data_demo,
            ]
        )
        info_message += "\nLegend: Queries | Query Time | Server Time | Total Time\n"
        _logger.info(info_message)

    def test_directory_search_read_benchmark(self):
        demo_uid = self.browse_ref("base.user_demo").id
        admin_uid = self.browse_ref("base.user_admin").id
        model = self.env["dms.directory"].with_context(bin_size=True)
        args = [[[], {"limit": 1}], [[], {"limit": 80}], [[], {"limit": 500}], [[]]]

        benchmark_data_super = ["Super"] + self._benchmark_function(
            model.sudo().search_read, args
        )
        benchmark_data_admin = ["Admin"] + self._benchmark_function(
            model.with_user(admin_uid).search_read, args
        )
        benchmark_data_demo = ["Demo"] + self._benchmark_function(
            model.with_user(demo_uid).search_read, args
        )

        info_message = "\n\nSearching and reading all fields with bin_size = True | "
        info_message += "Benchmark with Limit 1 / 80 / 500 / None (1500)\n\n"
        info_message += self._benchmark_table(
            [
                [
                    "User",
                    "Search Limit 1",
                    "Search Limit 80",
                    "Search Limit 500",
                    "Search No Limit",
                ],
                benchmark_data_super,
                benchmark_data_admin,
                benchmark_data_demo,
            ]
        )
        info_message += "\nLegend: Queries | Query Time | Server Time | Total Time\n"
        _logger.info(info_message)

    # ----------------------------------------------------------
    # Profiler
    # ----------------------------------------------------------

    @unittest.skip("Takes to long to be tested every time.")
    def test_file_search_read_profile_admin(self):
        @track_function()
        @profile(minimum_queries=35)
        def profile_function(model):
            model.search_read([])

        admin_uid = self.browse_ref("base.user_admin").id
        model = self.env["dms.file"].with_user(admin_uid)
        profile_function(model.with_context(bin_size=True))
