# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

import odoo.tests


@odoo.tests.tagged("post_install", "-at_install")
class TestDmsPortal(odoo.tests.HttpCase):
    def test_tour(self):
        self.phantom_js(
            "/",
            "odoo.__DEBUG__.services['web_tour.tour'].run('dms_portal_tour')",
            "odoo.__DEBUG__.services['web_tour.tour'].tours.dms_portal_tour.ready",
            login="portal",
        )
