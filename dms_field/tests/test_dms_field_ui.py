# Copyright 2026 Tecnativa - Carlos Roca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import base64

from odoo.tests import HttpCase, tagged

from .common import DmsFieldTestMixin


@tagged("post_install", "-at_install")
class TestDmsFieldTour(DmsFieldTestMixin, HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._create_partner_template()
        cls._create_partner_dms_view()
        cls.partner = (
            cls.env["res.partner"]
            .with_context(skip_track_dms_field_template=True)
            .create({"name": "Tour Partner"})
        )
        cls.root_directory = (
            cls.env["dms.field.template"]
            .with_context(res_model=cls.partner._name, res_id=cls.partner.id)
            .create_dms_directory()
        )
        directory_model = cls.env["dms.directory"]
        cls.folder = directory_model.create(
            {"name": "Tour Folder", "parent_id": cls.root_directory.id}
        )
        cls.target = directory_model.create(
            {"name": "Tour Target", "parent_id": cls.root_directory.id}
        )
        cls.file = cls.env["dms.file"].create(
            {
                "name": "tour.txt",
                "directory_id": cls.folder.id,
                "content": base64.b64encode(b"tour").decode(),
            }
        )
        cls.drag_file = cls.env["dms.file"].create(
            {
                "name": "drag.txt",
                "directory_id": cls.root_directory.id,
                "content": base64.b64encode(b"drag").decode(),
            }
        )

    def test_dms_field_tree_tour(self):
        self.assertTrue(self.root_directory)
        self.start_tour(
            f"/odoo/res.partner/{self.partner.id}",
            "dms_field_tree_tour",
            login="admin",
        )
        self.assertFalse(self.folder.exists())
        self.assertEqual(self.file.directory_id, self.target)
        self.assertEqual(self.drag_file.directory_id, self.target)
        self.assertEqual(self.drag_file.name, "dragged.txt")
        uploaded = self.target.file_ids.filtered(lambda f: f.name == "tour_upload.txt")
        self.assertEqual(len(uploaded), 1)
        self.assertEqual(uploaded.size, len(b"tour upload"))
