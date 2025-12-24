from . import models


def post_init_hook(env):
    env["ir.config_parameter"].sudo().set_param(
        "dms_file_sequence.display_name_pattern", "%(sequence_code)s - %(name)s"
    )
