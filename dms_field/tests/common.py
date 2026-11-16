# Copyright 2026 Tecnativa - Carlos Roca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


class DmsFieldTestMixin:
    """Create the records needed by the tests, as demo data is not
    loaded by default."""

    @classmethod
    def _create_partner_template(cls):
        # Only one template per model is allowed, reuse the demo one if loaded
        template = cls.env["dms.field.template"]._get_template_from_model("res.partner")
        if template:
            cls.template = template
            cls.storage = template.storage_id
            return template
        cls.storage = cls.env["dms.storage"].create(
            {"name": "Test Storage", "save_type": "database"}
        )
        cls.access_group = cls.env["dms.access.group"].create(
            {
                "name": "Test Access Group",
                "perm_create": True,
                "perm_write": True,
                "perm_unlink": True,
                "explicit_user_ids": [(6, 0, [cls.env.ref("base.user_admin").id])],
            }
        )
        # Root directory not linked to the template, to be used as parent
        cls.env["dms.directory"].create(
            {
                "name": "Test Root Directory",
                "is_root_directory": True,
                "storage_id": cls.storage.id,
                "group_ids": [(6, 0, cls.access_group.ids)],
            }
        )
        cls.template = cls.env["dms.field.template"].create(
            {
                "name": "Partner",
                "storage_id": cls.storage.id,
                "model_id": cls.env.ref("base.model_res_partner").id,
                "group_ids": [(6, 0, cls.access_group.ids)],
            }
        )
        cls.template.with_context(
            res_model=cls.template._name, res_id=cls.template.id
        ).create_dms_directory()
        cls.template.invalidate_recordset(["dms_directory_ids"])
        return cls.template

    @classmethod
    def _create_partner_dms_view(cls):
        view = cls.env.ref("dms_field.view_partner_form", raise_if_not_found=False)
        if view:
            return view
        return cls.env["ir.ui.view"].create(
            {
                "name": "res.partner.form.dms.test",
                "model": "res.partner",
                "inherit_id": cls.env.ref("base.view_partner_form").id,
                "arch": """
                    <notebook position="inside">
                        <page name="dms" string="DMS" invisible="not id">
                            <field name="dms_directory_ids" mode="dms_list" />
                        </page>
                    </notebook>
                """,
            }
        )
