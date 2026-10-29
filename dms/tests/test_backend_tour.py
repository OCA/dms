# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo.tests import HttpCase, tagged

from .common import StorageDatabaseBaseCase


@tagged("post_install", "-at_install")
class TestDmsBackendTour(HttpCase, StorageDatabaseBaseCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.directory.name = "Tour Directory"
        cls.file.name = "tour_file.txt"
        cls.child_directory = cls.create_directory(directory=cls.directory)
        cls.child_directory.name = "Tour Child Directory"
        cls.access_group.explicit_user_ids = [(4, cls.env.ref("base.user_admin").id)]
        cls.env.flush_all()

    def test_file_views_tour(self):
        self.start_tour(
            "/odoo/action-dms.action_dms_file",
            "dms_backend_file_views_tour",
            login="admin",
        )

    def test_directory_children_tour(self):
        self.start_tour(
            "/odoo/action-dms.action_dms_directory",
            "dms_backend_directory_children_tour",
            login="admin",
        )
