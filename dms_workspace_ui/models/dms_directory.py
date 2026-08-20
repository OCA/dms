from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError
from odoo.osv import expression


class DmsDirectory(models.Model):
    _inherit = "dms.directory"

    active = fields.Boolean(
        default=True,
        index=True,
        help="Archived folders are hidden from the normal Documents workspace.",
    )

    def dms_ui_set_archived(self, archived):
        self = self.with_context(active_test=False).exists()
        self._dms_ui_require_permission("permission_write")
        directory_ids = self.sudo()._dms_ui_recursive_directories().ids
        directories = self.with_context(active_test=False).browse(directory_ids)
        file_ids = directories.sudo()._dms_ui_recursive_files().ids
        files = self.env["dms.file"].with_context(active_test=False).browse(file_ids)
        directories._dms_ui_require_permission("permission_write")
        self._dms_ui_require_records_permission(files, "permission_write")
        files.write({"active": not archived})
        directories.write({"active": not archived})
        return True

    def dms_ui_get_share_action(self):
        self.ensure_one()
        self._dms_ui_require_permission("permission_read")
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "dms.wizard_dms_directory_share_action"
        )
        action["context"] = {
            **self.env.context,
            "active_model": self._name,
            "active_id": self.id,
            "active_ids": self.ids,
        }
        return action

    @api.model
    def dms_ui_child_directories(self, parent_id=False, search_domain=None):
        search_domain = search_domain or []
        archived = self.env["dms.file"]._dms_ui_archived_mode(search_domain)
        domain = [
            ("is_hidden", "=", False),
            ("active", "=", not archived),
            ("permission_read", "=", True),
        ]
        if parent_id:
            domain.append(("parent_id", "=", int(parent_id)))
        else:
            domain.append(("is_root_directory", "=", True))
        domain = expression.AND(
            [domain, self._dms_ui_directory_filter_domain(search_domain)]
        )
        directories = self.with_context(active_test=False).search(
            domain, order="name, id"
        )
        count_map = self._dms_ui_visible_child_count_map(
            directories, active=not archived
        )
        return [
            self._dms_ui_directory_payload(directory, count_map.get(directory.id, {}))
            for directory in directories
        ]

    @api.model
    def dms_ui_create_folder(self, parent_id, name):
        parent = self.browse(int(parent_id or 0)).exists()
        name = (name or "").strip()
        if not name:
            raise UserError(_("Folder name is required."))
        if parent:
            if not parent.active:
                raise UserError(_("Select an active destination folder."))
            parent._dms_ui_require_permission("permission_create")
            return self.create({"name": name, "parent_id": parent.id}).id

        storages = self.env["dms.storage"].search([("is_hidden", "=", False)])
        templates = storages.mapped("root_directory_ids").filtered(
            lambda directory: directory.permission_create
        )
        template = templates[:1]
        if not template:
            raise UserError(
                _(
                    "A root folder can only be created here when a visible "
                    "storage has an accessible root folder."
                )
            )
        return self.create(
            {
                "group_ids": [(6, 0, template.group_ids.ids)],
                "is_root_directory": True,
                "name": name,
                "storage_id": template.storage_id.id,
            }
        ).id

    def _dms_ui_directory_filter_domain(self, search_domain):
        domain = []

        def visit(item):
            if not isinstance(item, list | tuple):
                return
            if len(item) == 3 and isinstance(item[0], str):
                field, operator, value = item
                if field in {"name", "category_id", "tag_ids"}:
                    domain.append((field, operator, value))
                return
            for child in item:
                visit(child)

        visit(search_domain or [])
        return domain

    def _dms_ui_visible_child_count_map(self, directories, active=True):
        count_map = {
            directory.id: {"fileCount": 0, "folderCount": 0}
            for directory in directories
        }
        if not directories:
            return count_map

        file_groups = (
            self.env["dms.file"]
            .with_context(active_test=False)
            .read_group(
                [("directory_id", "in", directories.ids), ("active", "=", active)],
                ["directory_id"],
                ["directory_id"],
            )
        )
        for group in file_groups:
            directory_id = group["directory_id"] and group["directory_id"][0]
            if directory_id in count_map:
                count_map[directory_id]["fileCount"] = self._dms_ui_group_count(
                    group, "directory_id"
                )

        folder_groups = self.with_context(active_test=False).read_group(
            [("parent_id", "in", directories.ids), ("active", "=", active)],
            ["parent_id"],
            ["parent_id"],
        )
        for group in folder_groups:
            directory_id = group["parent_id"] and group["parent_id"][0]
            if directory_id in count_map:
                count_map[directory_id]["folderCount"] = self._dms_ui_group_count(
                    group, "parent_id"
                )

        return count_map

    def _dms_ui_group_count(self, group, field_name):
        return group.get("__count", group.get(f"{field_name}_count", 0))

    def _dms_ui_directory_payload(self, directory, counts=None):
        counts = counts or {}
        return {
            "type": "directory",
            "id": directory.id,
            "name": directory.with_context(directory_short_name=True).display_name,
            "parentId": directory.parent_id.id or False,
            "active": bool(directory.active),
            "humanSize": directory.human_size or "",
            "writeDate": fields.Datetime.to_string(directory.write_date),
            "fileCount": counts.get("fileCount", 0),
            "folderCount": counts.get("folderCount", 0),
            "permissions": {
                "create": bool(directory.permission_create),
                "read": bool(directory.permission_read),
                "write": bool(directory.permission_write),
                "unlink": bool(directory.permission_unlink),
            },
        }

    @api.model
    def dms_ui_paste(self, target_id, mode, items):
        target = self.browse(int(target_id)).exists()
        if not target or not target.active:
            raise UserError(_("Select an active destination folder."))
        target._dms_ui_require_permission("permission_create")
        if mode not in {"cut", "copy"}:
            raise UserError(_("Unsupported clipboard operation."))

        directories, files = self._dms_ui_get_items(items)
        directories = directories._dms_ui_top_level_directories()
        files = files.filtered(
            lambda item: not item.directory_id._dms_ui_has_selected_ancestor(
                directories
            )
        )

        if mode == "cut":
            directories._dms_ui_require_permission("permission_write")
            self._dms_ui_require_records_permission(files, "permission_write")
            for directory in directories:
                if directory.is_root_directory:
                    raise UserError(_("Root folders cannot be moved."))
                if target == directory or target._dms_ui_has_selected_ancestor(
                    directory
                ):
                    raise UserError(_("A folder cannot be moved inside itself."))
            directories.write({"parent_id": target.id})
            files.write({"directory_id": target.id})
            return self._dms_ui_paste_result(mode, target, directories, files)

        directories._dms_ui_require_permission("permission_read")
        self._dms_ui_require_records_permission(files, "permission_read")
        copied_directories = self.browse()
        copied_files = self.env["dms.file"]
        for directory in directories:
            values = {"parent_id": target.id}
            if directory.is_root_directory:
                values["is_root_directory"] = False
            copied_directories |= directory.copy(values)
        for file_record in files:
            copied_files |= file_record.copy({"directory_id": target.id})
        return self._dms_ui_paste_result(mode, target, copied_directories, copied_files)

    def _dms_ui_paste_result(self, mode, target, directories, files):
        return {
            "mode": mode,
            "target_directory_id": target.id,
            "directories": [
                {"id": directory.id, "name": directory.name}
                for directory in directories
            ],
            "files": [
                {"id": file_record.id, "name": file_record.name}
                for file_record in files
            ],
        }

    @api.model
    def _dms_ui_get_items(self, items):
        directories = self.with_context(active_test=False)
        files = self.env["dms.file"].with_context(active_test=False)
        seen = set()
        for item in items or []:
            item_type = item.get("type")
            item_id = int(item.get("id") or 0)
            key = (item_type, item_id)
            if item_type not in {"directory", "file"} or not item_id:
                raise UserError(_("Unsupported clipboard selection."))
            if key in seen:
                continue
            seen.add(key)
            record = (
                self.env["dms.directory" if item_type == "directory" else "dms.file"]
                .with_context(active_test=False)
                .browse(item_id)
                .exists()
            )
            if not record:
                raise AccessError(_("You cannot read every selected item."))
            self._dms_ui_require_records_permission(record, "permission_read")
            if item_type == "directory":
                directories |= record
            else:
                files |= record
        if not directories and not files:
            raise UserError(_("Select at least one item."))
        return directories, files

    def _dms_ui_recursive_directories(self):
        if not self:
            return self
        return self.with_context(active_test=False).search(
            [("id", "child_of", self.ids)]
        )

    def _dms_ui_recursive_files(self):
        if not self:
            return self.env["dms.file"].with_context(active_test=False)
        return (
            self.env["dms.file"]
            .with_context(active_test=False)
            .search([("directory_id", "child_of", self.ids)])
        )

    def _dms_ui_top_level_directories(self):
        return self.filtered(
            lambda directory: not directory.parent_id._dms_ui_has_selected_ancestor(
                self
            )
        )

    def _dms_ui_has_selected_ancestor(self, directories):
        current = self
        while current:
            if current in directories:
                return True
            current = current.parent_id
        return False

    def _dms_ui_require_permission(self, field_name):
        return self._dms_ui_require_records_permission(self, field_name)

    @api.model
    def _dms_ui_require_records_permission(self, records, field_name):
        operation = field_name.removeprefix("permission_")
        try:
            records._check_access_dms_record(operation)
        except AccessError:
            raise AccessError(
                _("You do not have permission to change every selected item.")
            ) from None
        return True
