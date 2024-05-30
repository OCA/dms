# Copyright 2017-2019 MuK IT GmbH.
# Copyright 2020 Creu Blanca
# Copyright 2021-2024 Tecnativa - Víctor Martínez
# Copyright 2024 Subteno - Timothée Vannier (https://www.subteno.com).
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import base64
import functools
import logging
import threading
import time
import uuid

from odoo.tests import Form, new_test_user

from odoo.addons.base.tests.common import BaseCommon

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


class DocumentsBaseCase(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # models
        cls.access_group_model = cls.env["dms.access.group"]
        cls.storage_model = cls.env["dms.storage"]
        cls.directory_model = cls.env["dms.directory"]
        cls.file_model = cls.env["dms.file"]
        cls.category_model = cls.env["dms.category"]
        cls.tag_model = cls.env["dms.tag"]
        cls.attachment_model = cls.env["ir.attachment"]
        cls.partner_model = cls.env["res.partner"]
        # users
        cls.user = new_test_user(cls.env, login="basic-user")
        cls.public_user = cls.env.ref("base.public_user")
        cls.dms_user = new_test_user(
            cls.env, login="dms-user", groups="dms.group_dms_user"
        )
        cls.dms_manager_user = new_test_user(
            cls.env, login="dms-manager", groups="dms.group_dms_manager"
        )
        cls.access_group = cls.access_group_model.create(
            {
                "name": "Test",
                "perm_create": True,
                "perm_write": True,
                "perm_unlink": True,
                "explicit_user_ids": [
                    (6, 0, [cls.dms_user.id, cls.dms_manager_user.id])
                ],
            }
        )

    @classmethod
    def content_base64(cls):
        return base64.b64encode(b"\xff data")

    @classmethod
    def create_storage(cls, save_type="database"):
        return cls.storage_model.create(
            {"name": "Test Storage", "save_type": save_type}
        )

    @classmethod
    def create_directory(cls, storage=False, directory=False, model_id=False):
        record = Form(cls.directory_model)
        record.name = uuid.uuid4().hex
        record.is_root_directory = True
        if model_id and storage.save_type == "attachment":
            # set storage_id_save_type to attachment, making model visible
            record.storage_id = storage
            record.model_id = model_id
        if directory:
            record.is_root_directory = False
            record.parent_id = directory
        else:
            record.storage_id = storage
            if not storage.inherit_access_from_parent_record:
                record.group_ids.add(cls.access_group)
        return record.save()

    @classmethod
    def create_file(cls, directory=False, content=False):
        record = Form(cls.file_model)
        record.name = uuid.uuid4().hex
        record.directory_id = directory
        record.content = content or cls.content_base64()
        return record.save()

    @classmethod
    def create_attachment(cls, name, res_model=False, res_id=False, content=False):
        return cls.attachment_model.create(
            {
                "name": name,
                "res_model": res_model,
                "res_id": res_id,
                "datas": content or cls.content_base64(),
            }
        )


class StorageAttachmentBaseCase(DocumentsBaseCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.storage = cls.create_storage(save_type="attachment")
        cls.storage.write(
            {
                "inherit_access_from_parent_record": True,
                "include_message_attachments": True,
                "model_ids": [(6, 0, [cls.env.ref("base.model_res_partner").id])],
            }
        )
        cls.partner_model_id = cls.env.ref("base.model_res_partner")
        cls.create_directory(storage=cls.storage, model_id=cls.partner_model_id)
        cls.partner = cls.partner_model.create({"name": "test partner"})
        cls.other_partner = cls.partner_model.create({"name": "other partner"})
        cls.model_partner = cls.env.ref("base.model_res_partner")

    @classmethod
    def _create_attachment(cls, name, partner=None):
        """
        Create an attachment for the partner model.
        If no partner is provided, the default partner is used.

        :param str name: The name of the attachment.
        :param odoo.model.res_partner partner: The partner to attach the document to.

        :return: The created attachment.
        :rtype: odoo.model.ir.attachment
        """
        if not partner:
            partner = cls.partner
        return cls.create_attachment(
            name=name,
            res_model=cls.partner_model._name,
            res_id=partner.id,
        )

    @classmethod
    def _get_partner_directory(cls, partner=False):
        if not partner:
            partner = cls.partner
        return cls.directory_model.search(
            [
                ("storage_id", "=", cls.storage.id),
                ("res_model", "=", cls.partner_model._name),
                ("res_id", "=", partner.id),
            ]
        )


class StorageDatabaseBaseCase(DocumentsBaseCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.storage = cls.create_storage(save_type="database")
        cls.directory = cls.create_directory(storage=cls.storage)
        cls.file = cls.create_file(directory=cls.directory)


class StorageFileBaseCase(DocumentsBaseCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.storage = cls.create_storage(save_type="file")
        cls.directory = cls.create_directory(storage=cls.storage)
        cls.file = cls.create_file(directory=cls.directory)
