# Copyright 2017-2019 MuK IT GmbH.
# Copyright 2020 Creu Blanca
# Copyright 2021-2022 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import base64
import functools
import logging
import os
import threading
import time
import uuid

from odoo import SUPERUSER_ID, _
from odoo.modules.module import get_module_resource
from odoo.tests import Form, common, new_test_user
from odoo.tools import convert_file

_path = os.path.dirname(os.path.dirname(__file__))
_logger = logging.getLogger(__name__)

# ----------------------------------------------------------
# Decorators
# ----------------------------------------------------------


def multi_users(users=False, reset=True, raise_exception=True, callback=False):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            user_list = users(self) if callable(users) else users
            test_results = []
            for user in user_list:
                self.cr.execute("SAVEPOINT test_multi_users")
                try:
                    if not isinstance(user[0], int):
                        self.uid = self.ref(user[0])
                    else:
                        self.uid = user[0]
                    if hasattr(self, callback):
                        callb = getattr(self, callback)
                        if callable(callb):
                            callb()
                    func(self, *args, **kwargs)
                except Exception as error:
                    test_results.append(
                        {
                            "user": user[0],
                            "expect": user[1],
                            "result": False,
                            "error": error,
                        }
                    )
                else:
                    test_results.append(
                        {
                            "user": user[0],
                            "expect": user[1],
                            "result": True,
                            "error": None,
                        }
                    )
                if reset:
                    self.env.cache.invalidate()
                    self.registry.clear_caches()
                    self.registry.reset_changes()
                    self.cr.execute("ROLLBACK TO SAVEPOINT test_multi_users")
                else:
                    self._cr.execute("RELEASE SAVEPOINT test_multi_users")
            test_fails = []
            for result in test_results:
                if result["expect"] != result["result"]:
                    message = "Test (%s) with user (%s) failed!"
                    _logger.info(message % (func.__name__, result["user"]))
                    if result["error"]:
                        _logger.error(result["error"], exc_info=True)
                    test_fails.append(result)
            if test_fails:
                message = "{} out of {} tests failed".format(
                    len(test_fails),
                    len(test_results),
                )
                if raise_exception and test_fails[0]["error"]:
                    raise test_fails[0]["error"]
                elif raise_exception:
                    raise Exception(_("Error has not been raised"))
                else:
                    _logger.info(message)
            return test_results

        return wrapper

    return decorator


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
                    query_count,
                    query_time,
                    remaining_time,
                    time_taken,
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


class DocumentsBaseCase(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.super_uid = SUPERUSER_ID
        # models
        self.access_group_model = self.env["dms.access.group"]
        self.storage_model = self.env["dms.storage"]
        self.directory_model = self.env["dms.directory"]
        self.file_model = self.env["dms.file"]
        self.category_model = self.env["dms.category"]
        self.tag_model = self.env["dms.tag"]
        self.attachment_model = self.env["ir.attachment"]
        self.partner_model = self.env["res.partner"]
        # users
        self.user = new_test_user(self.env, login="basic-user")
        self.public_user = self.env.ref("base.public_user")
        self.dms_user = new_test_user(
            self.env, login="dms-user", groups="dms.group_dms_user"
        )
        self.dms_manager_user = new_test_user(
            self.env, login="dms-manager", groups="dms.group_dms_manager"
        )
        self.access_group = self.access_group_model.create(
            {
                "name": "Test",
                "perm_create": True,
                "perm_write": True,
                "perm_unlink": True,
                "explicit_user_ids": [
                    (6, 0, [self.dms_user.id, self.dms_manager_user.id])
                ],
            }
        )

    def _setup_test_data(self):
        self.storage_model = self.storage_model.with_user(self.env.uid)
        self.directory_model = self.directory_model.with_user(self.env.uid)
        self.file_model = self.file_model.with_user(self.env.uid)
        self.category_model = self.category_model.with_user(self.env.uid)
        self.tag_model = self.tag_model.with_user(self.env.uid)
        self.attachment_model = self.attachment_model.with_user(self.env.uid)

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

    def multi_users(self, super_user=True, admin=True, demo=True):
        return [
            [self.super_uid, super_user],
            [self.dms_manager_user.id, admin],
            [self.dms_user.id, demo],
        ]

    def content_base64(self):
        return base64.b64encode(b"\xff data")

    def create_storage(self, save_type="database"):
        return self.storage_model.create(
            {"name": "Test Storage", "save_type": save_type}
        )

    def create_directory(self, storage=False, directory=False, res_model=False):
        record = Form(self.directory_model)
        record.name = uuid.uuid4().hex
        record.is_root_directory = True
        record.res_model = res_model
        if directory:
            record.is_root_directory = False
            record.parent_id = directory
        else:
            record.storage_id = storage
            if not storage.inherit_access_from_parent_record:
                record.group_ids.add(self.access_group)
        return record.save()

    def create_file(self, directory=False, content=False):
        record = Form(self.file_model)
        record.name = uuid.uuid4().hex
        record.directory_id = directory
        record.content = content or self.content_base64()
        return record.save()

    def create_attachment(self, name, res_model=False, res_id=False, content=False):
        return self.attachment_model.create(
            {
                "name": name,
                "res_model": res_model,
                "res_id": res_id,
                "datas": content or self.content_base64(),
            }
        )


class StorageAttachmentBaseCase(DocumentsBaseCase):
    def setUp(self):
        super().setUp()
        self.storage = self.create_storage(save_type="attachment")
        self.storage.write(
            {
                "inherit_access_from_parent_record": True,
                "include_message_attachments": True,
                "model_ids": [(6, 0, [self.env.ref("base.model_res_partner").id])],
            }
        )
        self.create_directory(storage=self.storage, res_model=self.partner_model._name)
        self.partner = self.partner_model.create({"name": "test partner"})
        self.model_partner = self.env.ref("base.model_res_partner")

    def _create_attachment(self, name):
        return self.create_attachment(
            name=name,
            res_model=self.partner_model._name,
            res_id=self.partner.id,
        )

    def _get_partner_directory(self):
        return self.directory_model.search(
            [
                ("storage_id", "=", self.storage.id),
                ("res_model", "=", self.partner_model._name),
                ("res_id", "=", self.partner.id),
            ]
        )


class StorageDatabaseBaseCase(DocumentsBaseCase):
    def setUp(self):
        super().setUp()
        self.storage = self.create_storage(save_type="database")
        self.directory = self.create_directory(storage=self.storage)
        self.file = self.create_file(directory=self.directory)


class StorageFileBaseCase(DocumentsBaseCase):
    def setUp(self):
        super().setUp()
        self.storage = self.create_storage(save_type="file")
        self.directory = self.create_directory(storage=self.storage)
        self.file = self.create_file(directory=self.directory)
