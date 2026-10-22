# Copyright 2026 Windweaver
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import new_test_user
from odoo.tools import mute_logger

from odoo.addons.base.tests.common import BaseCommon


class TestProjectDmsField(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, test_dms_field=True))
        cls.template = cls.env.ref("project_dms_field.field_template_project")
        cls.storage = cls.template.storage_id
        cls.access_group = cls.template.group_ids
        cls.env["dms.directory"].create(
            {
                "name": "Specifications",
                "parent_id": cls.template.dms_directory_ids[0].id,
                "storage_id": cls.storage.id,
            }
        )
        cls.env["dms.directory"].create(
            {
                "name": "Deliverables",
                "parent_id": cls.template.dms_directory_ids[0].id,
                "storage_id": cls.storage.id,
            }
        )
        cls.user = new_test_user(cls.env, login="test-project-user")
        cls.project_model = cls.env["project.project"]

    def test_project_create_01(self):
        project = self.project_model.create({"name": "Test project"})
        # Manually refresh, similar to UX
        # dms_field/static/src/views/dms_list/dms_list_renderer.esm.js#L450
        project.invalidate_model()
        directory = project.dms_directory_ids
        self.assertEqual(len(directory), 1)
        self.assertEqual(directory.storage_id, self.storage)
        group_custom = directory.group_ids.filtered("dms_field_ref")
        self.assertIn(self.access_group, directory.group_ids)
        self.assertNotIn(self.user, group_custom.explicit_user_ids)
        child_directory_names = directory.mapped("child_directory_ids.name")
        self.assertIn("Specifications", child_directory_names)
        self.assertIn("Deliverables", child_directory_names)

    def test_project_create_02(self):
        project = self.project_model.create(
            {
                "name": "Test project",
                "user_id": self.user.id,
            }
        )
        # Manually refresh, similar to UX
        # dms_field/static/src/views/dms_list/dms_list_renderer.esm.js#L450
        project.invalidate_model()
        group_custom = project.dms_directory_ids.group_ids.filtered("dms_field_ref")
        self.assertIn(self.user, group_custom.explicit_user_ids)

    def test_project_write_user(self):
        project = self.project_model.create({"name": "Test project"})
        project.invalidate_recordset()
        directory = project.dms_directory_ids
        self.assertEqual(len(directory), 1)
        group_custom = directory.group_ids.filtered("dms_field_ref")
        self.assertFalse(group_custom.explicit_user_ids)
        project.write({"user_id": self.user.id})
        self.assertIn(self.user, group_custom.explicit_user_ids)

    @mute_logger("odoo.models.unlink")
    def test_project_full_process(self):
        project = self.project_model.create(
            {
                "name": "Test project",
                "user_id": self.user.id,
            }
        )
        # Manually refresh, similar to UX
        # dms_field/static/src/views/dms_list/dms_list_renderer.esm.js#L450
        project.invalidate_model()
        directory = project.dms_directory_ids[0]
        group_custom = directory.group_ids.filtered("dms_field_ref")
        self.assertIn(self.user, group_custom.explicit_user_ids)
        project.write({"user_id": False})
        self.assertFalse(group_custom.explicit_user_ids)
        project.write({"user_id": self.user.id})
        self.assertIn(self.user, group_custom.explicit_user_ids)
        project.unlink()
        self.assertFalse(directory.exists())
        self.assertFalse(group_custom.exists())
