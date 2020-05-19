# Copyright 2017-2019 MuK IT GmbH.
# Copyright 2020 Creu Blanca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

import logging
import os

from odoo.tools import mute_logger

from .test_directory import DirectoryTestCase

_path = os.path.dirname(os.path.dirname(__file__))
_logger = logging.getLogger(__name__)


class DirectoryActionTestCase(DirectoryTestCase):
    def setUp(self):
        super(DirectoryActionTestCase, self).setUp()
        self.params = self.env["ir.config_parameter"].sudo()
        self.params.set_param("mail.catchall.domain", "mydomain.com")
        self._setup_test_data()

    @mute_logger("odoo.addons.mail.mail_thread")
    def test_mail_alias_files(self):
        self.create_directory(storage=self.new_storage).write(
            {"alias_process": "files", "alias_name": "directory+test"}
        )
        with open(os.path.join(_path, "tests", "data", "mail01.eml"), "r") as file:
            self.env["mail.thread"].message_process(None, file.read())
        with open(os.path.join(_path, "tests", "data", "mail02.eml"), "r") as file:
            self.env["mail.thread"].message_process(None, file.read())

    @mute_logger("odoo.addons.mail.mail_thread")
    def test_mail_alias_directory(self):
        self.create_directory(storage=self.new_storage).write(
            {"alias_process": "directory", "alias_name": "directory+test"}
        )
        with open(os.path.join(_path, "tests", "data", "mail01.eml"), "r") as file:
            self.env["mail.thread"].message_process(None, file.read())
        with open(os.path.join(_path, "tests", "data", "mail02.eml"), "r") as file:
            self.env["mail.thread"].message_process(None, file.read())
