# Copyright 2026 Tecnativa - Carlos Roca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import Command


class HrDmsFieldTestMixin:
    """Create the records needed by the tests, as demo data is not
    loaded by default."""

    @classmethod
    def _create_employee_template(cls):
        # Only one template per model is allowed, reuse the demo one if loaded
        template = cls.env["dms.field.template"]._get_template_from_model("hr.employee")
        if template:
            return template
        storage = cls.env["dms.storage"].create(
            {"name": "Test Employee Storage", "save_type": "database"}
        )
        access_group = cls.env["dms.access.group"].create(
            {
                "name": "Test Employee Access Group",
                "group_ids": [Command.link(cls.env.ref("hr.group_hr_user").id)],
                "perm_create": True,
                "perm_write": True,
                "perm_unlink": True,
            }
        )
        template = cls.env["dms.field.template"].create(
            {
                "name": "Employee",
                "storage_id": storage.id,
                "model_id": cls.env.ref("hr.model_hr_employee").id,
                "user_field_id": cls.env.ref("hr.field_hr_employee__user_id").id,
                "group_ids": [Command.set(access_group.ids)],
                "directory_format_name": "{{object.display_name}} (employee)",
            }
        )
        template.with_context(
            res_model=template._name, res_id=template.id
        ).create_dms_directory()
        template.invalidate_recordset(["dms_directory_ids"])
        return template
