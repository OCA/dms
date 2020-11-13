# Copyright 2017-2019 MuK IT GmbH.
# Copyright 2020 Creu Blanca
# Copyright 2020 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import base64
import functools
import logging
import os
import threading
import time
import uuid

from odoo.modules.module import get_module_resource
from odoo.tests import common
from odoo.tools import convert_file

_path = os.path.dirname(os.path.dirname(__file__))
_logger = logging.getLogger(__name__)

# ----------------------------------------------------------
# Decorators
# ----------------------------------------------------------


def track_function(
    max_query_count=None, max_query_time=None, max_time=None, return_tracking=False
):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            tracking_parameters = [func.__name__]
            threading.current_thread().query_time = 0
            threading.current_thread().query_count = 0
            threading.current_thread().perf_t0 = time.time()
            result = func(*args, **kwargs)
            message = "%s" % func.__name__
            if args and hasattr(args[0], "uid"):
                message = " (%s)" % args[0].uid
            if hasattr(threading.current_thread(), "query_count"):
                query_count = threading.current_thread().query_count
                query_time = threading.current_thread().query_time
                perf_t0 = threading.current_thread().perf_t0
                remaining_time = time.time() - perf_t0 - query_time
                time_taken = query_time + remaining_time
                message += " - {} Q {:.3f}s QT {:.3f}s OT {:.3f}s TT".format(
                    query_count, query_time, remaining_time, time_taken,
                )
                tracking_parameters += [
                    query_count,
                    query_time,
                    remaining_time,
                    time_taken,
                ]
                if max_query_count and query_count > max_query_count:
                    raise AssertionError("More than %s queries" % max_query_count)
                if max_query_time and query_time > max_query_time:
                    raise AssertionError(
                        "Queries took longer than %.3fs" % max_query_time
                    )
                if max_time and time_taken > max_time:
                    raise AssertionError("Function took longer than %.3fs" % max_time)
            if not return_tracking:
                _logger.info(message)
            if return_tracking:
                return result, tracking_parameters
            return result

        return wrapper

    return decorator


# ----------------------------------------------------------
# Test Cases
# ----------------------------------------------------------


class DocumentsBaseCase(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin_uid = cls.env.ref("base.user_admin").id
        cls.storage = cls.env["dms.storage"]
        cls.directory = cls.env["dms.directory"]
        cls.file = cls.env["dms.file"]
        cls.category = cls.env["dms.category"]
        cls.tag = cls.env["dms.tag"]
        cls.attachment = cls.env["ir.attachment"]

    def _setup_test_data(self):
        self.storage = self.storage.with_user(self.env.uid)
        self.directory = self.directory.with_user(self.env.uid)
        self.file = self.file.with_user(self.env.uid)
        self.category = self.category.with_user(self.env.uid)
        self.tag = self.tag.with_user(self.env.uid)
        self.attachment = self.attachment.with_user(self.env.uid)

    def _load(self, module, *args):
        convert_file(
            self.cr,
            "dms",
            get_module_resource(module, *args),
            {},
            "init",
            False,
            "test",
            self.registry._assertion_report,
        )

    def create_storage(self, save_type="database", sudo=False):
        model = self.storage.sudo() if sudo else self.storage
        return model.create({"name": "Test Storage", "save_type": save_type})

    def create_directory(self, storage=False, directory=False, sudo=False):
        model = self.directory.sudo() if sudo else self.directory
        if not storage and not directory:
            storage = self.create_storage(sudo=sudo)
        if directory:
            return model.create(
                {
                    "name": uuid.uuid4().hex,
                    "is_root_directory": False,
                    "parent_id": directory.id,
                }
            )
        return model.create(
            {
                "name": uuid.uuid4().hex,
                "is_root_directory": True,
                "root_storage_id": storage.id,
            }
        )

    def create_file(self, directory=False, content=False, storage=False, sudo=False):
        model = self.file.sudo() if sudo else self.file
        if not directory:
            directory = self.create_directory(storage=storage, sudo=sudo)
        return model.create(
            {
                "name": uuid.uuid4().hex,
                "directory_id": directory.id,
                "content": content or base64.b64encode(b"\xff data"),
            }
        )

    def create_file_with_context(
        self, context, directory=False, content=False, storage=False, sudo=False
    ):
        model = self.file.sudo() if sudo else self.file
        if not directory:
            directory = self.create_directory(storage=storage, sudo=sudo)
        return model.with_context(context).create(
            {
                "name": uuid.uuid4().hex,
                "directory_id": directory.id,
                "content": content or base64.b64encode(b"\xff data"),
            }
        )

    def create_attachment(
        self, name, res_model=False, res_id=False, content=False, sudo=False
    ):
        model = self.attachment.sudo() if sudo else self.attachment
        return model.create(
            {
                "name": name,
                "res_model": res_model,
                "res_id": res_id,
                "datas": content or base64.b64encode(b"\xff data"),
            }
        )
