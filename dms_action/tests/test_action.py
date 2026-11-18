# Copyright 2022 CreuBlanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError

from odoo.addons.dms.tests.common import DocumentsBaseCase


class TestAction(DocumentsBaseCase):
    def setUp(self):
        super().setUp()
        self.server_action = self.env["ir.actions.server"].create(
            {
                "name": "server action",
                "model_id": self.env.ref("dms.model_dms_file").id,
                "state": "code",
                "code": "record.lock()",
            }
        )
        self.storage = self.create_storage(save_type="database")
        self.directory = self.create_directory(storage=self.storage)
        self.action = self.env["dms.action"].create(
            {
                "name": "Action",
                "kind": "server_action",
                "action_id": self.server_action.id,
                "dms_directory_ids": [(4, self.directory.id)],
            }
        )
        self.file = self.create_file(directory=self.directory)

    def test_action(self):
        self.assertFalse(self.file.locked_by)
        self.file.execute_action(kwargs={"action_id": self.action.id})
        self.assertTrue(self.file.locked_by)

    def test_action_not_allowed(self):
        self.action.dms_directory_ids = False
        with self.assertRaises(ValidationError):
            self.file.execute_action(kwargs={"action_id": self.action.id})
        self.assertFalse(self.file.locked_by)

    def test_action_inherited_by_descendants(self):
        child = self.create_directory(directory=self.directory)
        grandchild = self.create_directory(directory=child)
        descendant_file = self.create_file(directory=grandchild)
        self.assertTrue(descendant_file.with_actions)
        self.assertIn(str(self.action.id), descendant_file.action_button)
        descendant_file.execute_action(kwargs={"action_id": self.action.id})
        self.assertTrue(descendant_file.locked_by)

    def test_action_not_inherited_by_parent_or_sibling(self):
        child = self.create_directory(directory=self.directory)
        sibling = self.create_directory(directory=self.directory)
        sibling_file = self.create_file(directory=sibling)
        self.action.dms_directory_ids = child
        for file in self.file | sibling_file:
            self.assertFalse(file.with_actions)
            with self.assertRaises(ValidationError):
                file.execute_action(kwargs={"action_id": self.action.id})

    def test_inherited_action_group_restriction(self):
        child = self.create_directory(directory=self.directory)
        child_file = self.create_file(directory=child)
        self.action.group_ids = self.env["res.groups"].create(
            {"name": "Restricted inherited DMS action"}
        )
        self.assertFalse(child_file.with_actions)
        with self.assertRaises(ValidationError):
            child_file.execute_action(kwargs={"action_id": self.action.id})

    def test_action_group_restriction(self):
        group = self.env["res.groups"].create({"name": "DMS action test group"})
        self.action.group_ids = group
        self.assertFalse(self.file.with_actions)
        self.assertFalse(self.file.action_button)
        with self.assertRaises(ValidationError):
            self.file.execute_action(kwargs={"action_id": self.action.id})
        self.assertFalse(self.file.locked_by)

    def test_action_group_allowed(self):
        self.action.group_ids = self.env.user.groups_id[:1]
        self.assertTrue(self.file.with_actions)
        self.assertIn(str(self.action.id), self.file.action_button)
        self.file.execute_action(kwargs={"action_id": self.action.id})
        self.assertTrue(self.file.locked_by)

    def _create_tag_action(self, operation, tag, sequence=10):
        return self.env["dms.action.tag.action"].create(
            {
                "dms_action_id": self.action.id,
                "action": operation,
                "category_id": tag.category_id.id,
                "tag_id": tag.id,
                "sequence": sequence,
            }
        )

    def _create_action_tags(self):
        category = self.env["dms.category"].create({"name": "Action category"})
        other_category = self.env["dms.category"].create(
            {"name": "Other action category"}
        )
        tags = self.env["dms.tag"].create(
            [
                {"name": "Old tag", "category_id": category.id},
                {"name": "New tag", "category_id": category.id},
                {"name": "Other tag", "category_id": other_category.id},
            ]
        )
        return tags[0], tags[1], tags[2]

    def test_tag_action_add(self):
        old, new, other = self._create_action_tags()
        self.file.tag_ids = old | other
        action = self._create_tag_action("add", new)
        action.execute_actions(self.file)
        self.assertEqual(self.file.tag_ids, old | new | other)
        action.execute_actions(self.file)
        self.assertEqual(self.file.tag_ids, old | new | other)

    def test_tag_action_remove(self):
        old, new, other = self._create_action_tags()
        self.file.tag_ids = old | other
        action = self._create_tag_action("remove", old)
        action.execute_actions(self.file)
        self.assertEqual(self.file.tag_ids, other)
        action.execute_actions(self.file)
        self.assertEqual(self.file.tag_ids, other)
        self.assertTrue(old.exists(), "Removing a link must preserve the tag")

    def test_tag_action_replace(self):
        old, new, other = self._create_action_tags()
        self.file.tag_ids = old | other
        action = self._create_tag_action("replace", new)
        action.execute_actions(self.file)
        self.assertEqual(self.file.tag_ids, new | other)
        action.execute_actions(self.file)
        self.assertEqual(self.file.tag_ids, new | other)
        self.assertTrue(old.exists())

    def test_tag_action_replace_empty_category(self):
        old, new, other = self._create_action_tags()
        self.file.tag_ids = other
        self._create_tag_action("replace", new).execute_actions(self.file)
        self.assertEqual(self.file.tag_ids, new | other)

    def test_tag_actions_sequence_and_server_action(self):
        old, new, other = self._create_action_tags()
        self.file.tag_ids = old | other
        # Create in reverse order to check sequence rather than creation order.
        self._create_tag_action("remove", new, sequence=20)
        self._create_tag_action("replace", new, sequence=10)
        self.file.execute_action(kwargs={"action_id": self.action.id})
        self.assertEqual(self.file.tag_ids, other)
        self.assertTrue(self.file.locked_by)

    def test_tag_action_category_mismatch(self):
        old, new, other = self._create_action_tags()
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            self.env["dms.action.tag.action"].create(
                {
                    "dms_action_id": self.action.id,
                    "action": "add",
                    "category_id": other.category_id.id,
                    "tag_id": new.id,
                }
            )
        action = self._create_tag_action("add", new)
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            action.category_id = other.category_id
