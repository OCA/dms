# Copyright 2026 Tecnativa - Adasat Torres
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import Command


def _create_default_storage(env, company):
    return env["dms.storage"].create(
        {
            "name": f"EE storage - {company.name}",
            "save_type": "file",
            "company_id": company.id,
        }
    )


def _search_or_create(env, model, domain, vals):
    Model = env[model]
    res = Model.search(domain)
    if not res:
        res = Model.create(vals)
    return res


def _prepare_dms_tags_vals(ee_tag, category_id):
    return {"name": ee_tag.name, "category_id": category_id}


def _prepare_category_vals(ee_category):
    return {"name": ee_category.name}


def _prepare_directory_vals(ee_folder, **kwargs):
    return {"name": ee_folder.name, **kwargs}


def _prepare_file_vals(ee_document, directory_id, tag_ids):
    return {
        "name": ee_document.name,
        "extension": ee_document.file_extension,
        "content": ee_document.datas,
        "directory_id": directory_id.id,
        "tag_ids": [Command.set(tag_ids.ids if tag_ids else [])],
    }


def _search_create_category(env, ee_facet):
    return _search_or_create(
        env,
        "dms.category",
        [("name", "ilike", ee_facet.name)],
        _prepare_category_vals(ee_facet),
    )


def _search_create_tag(env, ee_tags, category=False):
    tags = env["dms.tag"]
    for ee_tag in ee_tags:
        tags += _search_or_create(
            env,
            "dms.tag",
            [("name", "ilike", ee_tag.name)],
            _prepare_dms_tags_vals(ee_tag, category.id if category else False),
        )
    return tags


def _create_categories_and_tags(env, ee_facets):
    for ee_facet in ee_facets:
        categ = _search_create_category(env, ee_facet)
        _search_create_tag(env, ee_facet.tag_ids, categ)


def _search_create_directory(env, folder, **kwargs):
    return _search_or_create(
        env,
        "dms.directory",
        [("name", "=", folder.name)],
        _prepare_directory_vals(folder, **kwargs),
    )


def _search_create_admin_dms_access_group(env):
    return _search_create_dms_access_group(
        env,
        **{
            "name": "Admin",
            "group_ids": [Command.link(env.ref("base.group_system").id)],
            "perm_create": True,
            "perm_write": True,
            "perm_unlink": True,
        },
    )


def _search_create_dms_access_group(env, **kwargs):
    return _search_or_create(
        env, "dms.access.group", [("name", "ilike", kwargs.get("name", False))], kwargs
    )


def _create_file(env, ee_document, directory):
    tags = _search_create_tag(env, ee_document.tag_ids)
    _search_or_create(
        env,
        "dms.file",
        [("name", "=", ee_document.name), ("directory_id", "=", directory.id)],
        _prepare_file_vals(ee_document, directory, tags),
    )


def _create_directory_and_files(env, ee_folder, storage):
    admin_access_group = _search_create_admin_dms_access_group(env)
    vals = {
        "is_root_directory": True,
        "storage_id": storage.id,
        "group_ids": [Command.link(admin_access_group.id)],
    }
    if ee_folder.read_group_ids:
        read_access_group = _search_create_dms_access_group(
            env,
            **{
                "name": f"{ee_folder.name} - Read",
                "group_ids": [Command.set(ee_folder.read_group_ids.ids)],
                "perm_create": False,
                "perm_write": False,
                "perm_unlink": False,
            },
        )
        vals["group_ids"].append(Command.link(read_access_group.id))
    if ee_folder.group_ids:
        write_access_group = _search_create_dms_access_group(
            env,
            **{
                "name": f"{ee_folder.name} - Write",
                "group_ids": [Command.set(ee_folder.group_ids.ids)],
                "perm_create": True,
                "perm_write": True,
                "perm_unlink": False,
            },
        )
        vals["group_ids"].append(Command.link(write_access_group.id))
    if ee_folder.parent_folder_id:
        vals["parent_id"] = _search_create_directory(
            env, ee_folder.parent_folder_id, **vals
        ).id
        vals["is_root_directory"] = False
        vals.pop("storage_id")
    if ee_folder.facet_ids:
        vals["category_id"] = _search_create_category(env, ee_folder.facet_ids[0]).id
    directory = _search_create_directory(env, ee_folder, **vals)
    for document in ee_folder.document_ids.filtered(lambda d: d.type == "binary"):
        _create_file(env, document, directory)


def post_init_hook(env):
    if not env["ir.module.module"].search(
        [("name", "=", "documents"), ("state", "=", "installed")]
    ):
        return
    DocumentsFolder = env["documents.folder"]
    for company in env["res.company"].search([]):
        if not DocumentsFolder.search([], limit=1):
            continue
        storage = _create_default_storage(env, company)
        for folder in DocumentsFolder.search([]):
            _create_categories_and_tags(env, folder.mapped("facet_ids"))
            _create_directory_and_files(env, folder, storage)
