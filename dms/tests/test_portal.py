# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

import odoo.tests


@odoo.tests.tagged("post_install", "-at_install")
class TestDmsPortal(odoo.tests.HttpCase):
    def test_tour(self):
        self.start_tour("/", "dms_portal_tour", login="portal")
