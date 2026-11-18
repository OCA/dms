# Copyright 2026 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import exceptions

from .common import Common


class TestDmsDirectory(Common):
    def test_access_group_no_state_permission(self):
        """If no Access Group has "Can Change Directory State" enabled,
        the State cannot be changed.
        """
        # Arrange
        directory = self.directory
        directory.group_ids += self.no_change_access_group

        # Act
        with self.assertRaises(exceptions.AccessError) as ae:
            directory.with_user(self.demo_user).state = "obsolete"
        exc_message = ae.exception.args[0]

        # Assert
        self.assertIn("change the state", exc_message)

    def test_access_group_with_state_permission(self):
        """If an Access Group has "Can Change Directory State" enabled,
        the State can be changed.
        """
        # Arrange
        directory = self.directory
        directory.group_ids += self.change_access_group

        # Act
        directory.with_user(self.demo_user).state = "obsolete"

        # Assert
        self.assertEqual(directory.state, "obsolete")
