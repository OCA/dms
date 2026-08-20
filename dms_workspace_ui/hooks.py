def post_init_hook(env):
    env.cr.execute("UPDATE dms_directory SET active = TRUE WHERE active IS NULL")
    env["res.config.settings"]._dms_ui_apply_menu_visibility()
