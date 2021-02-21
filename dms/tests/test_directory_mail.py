# Copyright 2017-2019 MuK IT GmbH.
# Copyright 2020 Creu Blanca
# Copyright 2020 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

import logging
import os

from odoo.tools import mute_logger

from .test_directory import DirectoryTestCase

_path = os.path.dirname(os.path.dirname(__file__))
_logger = logging.getLogger(__name__)


class DirectoryActionTestCase(DirectoryTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.params = cls.env["ir.config_parameter"].sudo()
        cls.params.set_param("mail.catchall.domain", "mydomain.com")
        cls._setup_test_data(cls)
        cls.directory_test = cls.create_directory(cls, storage=cls.new_storage)

    @mute_logger("odoo.addons.mail.mail_thread")
    def test_mail_alias_files(self):
        self.directory.write({"alias_process": "files", "alias_name": "directory+test"})
        with open(os.path.join(_path, "tests", "data", "mail01.eml"), "r") as file:
            with self.assertRaises(ValueError):
                self.env["mail.thread"].message_process(None, file.read())
        with open(os.path.join(_path, "tests", "data", "mail02.eml"), "r") as file:
            with self.assertRaises(ValueError):
                self.env["mail.thread"].message_process(None, file.read())

    @mute_logger("odoo.addons.mail.mail_thread")
    def test_mail_alias_directory(self):
        self.directory.write(
            {"alias_process": "directory", "alias_name": "directory+test"}
        )
        with open(os.path.join(_path, "tests", "data", "mail01.eml"), "r") as file:
            with self.assertRaises(ValueError):
                self.env["mail.thread"].message_process(None, file.read())
        with open(os.path.join(_path, "tests", "data", "mail02.eml"), "r") as file:
            with self.assertRaises(ValueError):
                self.env["mail.thread"].message_process(None, file.read())
