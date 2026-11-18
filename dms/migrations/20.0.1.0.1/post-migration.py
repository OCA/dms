# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    """The maximum upload size had no default in the settings: saving them
    before the parameter existed stored 0, which refused every upload. Remove
    a zero or negative value so the default (25 MB) applies again."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    params = env["ir.config_parameter"].sudo()
    if params.get_int("dms.binary_max_size", 25) <= 0:
        params.set_int("dms.binary_max_size", None)
