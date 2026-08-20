from odoo import _, api, models
from odoo.exceptions import AccessError
from odoo.osv import expression


class DmsFile(models.Model):
    _inherit = "dms.file"

    def dms_ui_get_share_action(self):
        self.ensure_one()
        if not self.permission_read:
            raise AccessError(_("You cannot share this file."))
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "dms.wizard_dms_file_share_action"
        )
        action["context"] = {
            **self.env.context,
            "active_model": self._name,
            "active_id": self.id,
            "active_ids": self.ids,
        }
        return action

    @api.model
    def search_panel_select_range(self, field_name, **kwargs):
        if field_name != "directory_id" or not self.env.context.get("dms_ui_workspace"):
            return super().search_panel_select_range(field_name, **kwargs)

        archived = self._dms_ui_archived_mode(kwargs.get("search_domain", []))
        directory_model = self.env["dms.directory"].with_context(active_test=False)
        file_model = self.with_context(active_test=False)

        if archived:
            file_domain = expression.AND(
                [kwargs.get("search_domain", []), [("is_hidden", "=", False)]]
            )
            archived_files = file_model.search(file_domain)
            archived_directories = directory_model.search(
                [("is_hidden", "=", False), ("active", "=", False)]
            )
            directories = archived_directories | archived_files.mapped("directory_id")
            current = directories
            while current:
                parents = current.mapped("parent_id") - directories
                if not parents:
                    break
                directories |= parents
                current = parents
        else:
            directories = directory_model.search(
                [("is_hidden", "=", False), ("active", "=", True)]
            )

        directories = directories.sorted(
            lambda directory: directory.complete_name or ""
        )
        all_ids = set(directories.ids)
        count_domain = expression.AND(
            [
                kwargs.get("search_domain", []),
                [
                    ("is_hidden", "=", False),
                    ("active", "=", not archived),
                ],
            ]
        )
        counts = {
            directory.id: count
            for directory, count in file_model._read_group(
                count_domain,
                ["directory_id"],
                ["__count"],
            )
            if directory
        }
        values = []
        for directory in directories:
            values.append(
                {
                    "id": directory.id,
                    "display_name": directory.with_context(
                        directory_short_name=True
                    ).display_name,
                    "parent_id": (
                        directory.parent_id.id
                        if directory.parent_id.id in all_ids
                        else False
                    ),
                    "__count": counts.get(directory.id, 0),
                    "dms_ui_archived": not directory.active,
                    "dms_ui_permissions": {
                        "create": bool(directory.permission_create),
                        "read": bool(directory.permission_read),
                        "write": bool(directory.permission_write),
                        "unlink": bool(directory.permission_unlink),
                    },
                }
            )
        return {"parent_field": "parent_id", "values": values}

    @api.model
    def _dms_ui_archived_mode(self, domain):
        leaves = []

        def visit(item):
            if isinstance(item, list | tuple):
                if len(item) == 3 and isinstance(item[0], str):
                    leaves.append(tuple(item))
                else:
                    for child in item:
                        visit(child)

        visit(domain or [])
        return ("active", "=", False) in leaves and (
            "active",
            "!=",
            False,
        ) not in leaves
