# Copyright 2025 Kencove (https://www.kencove.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
import mimetypes
import os
import threading
from collections import defaultdict
from random import randint

from openupgradelib import openupgrade, openupgrade_merge_records
from pathvalidate import sanitize_filename
from PIL import Image
from psycopg2.sql import SQL, Identifier

from odoo import SUPERUSER_ID, Command, api, models
from odoo.exceptions import UserError
from odoo.tools import sql, table_exists
from odoo.tools.misc import get_lang, split_every

from odoo.addons.dms.models.dms_file import File

from .tools import file as file_utils

_logger = logging.getLogger(__name__)


def _default_color():
    """Generate a random color index."""
    return randint(1, 11)


def _normalize(text):
    return (text or "").strip().lower()


def _preprocess_filename(original_name):
    """Sanitize and split filename into name and extension."""
    if original_name.startswith(".") and len(original_name) > 1:
        base_name = "unnamed"
        extension = original_name
    else:
        base_name, extension = os.path.splitext(original_name)
        if not extension and base_name.startswith("."):
            base_name = "unnamed"
            extension = original_name
        elif not base_name:
            base_name = "unnamed"
    sanitized_base = sanitize_filename(base_name, replacement_text="_")
    sanitized_ext = sanitize_filename(extension, replacement_text="_")
    if not sanitized_base:
        sanitized_base = "unnamed"
    sanitized_name = f"{sanitized_base}{sanitized_ext}"
    if original_name != sanitized_name:
        _logger.debug("Sanitized filename: '%s' to '%s'", original_name, sanitized_name)
    return sanitized_name, sanitized_ext


def _get_or_create_default_storage(env):
    """Get or create a default DMS storage of type 'file'."""
    Storage = env["dms.storage"]
    db_storage = Storage.search([("save_type", "=", "file")], limit=1)
    if not db_storage:
        db_storage = Storage.create(
            {
                "name": "Migrated DB Storage (from EE)",
                "save_type": "file",
            }
        )
        _logger.info("Created default file storage (ID: %s)", db_storage.id)
    return db_storage


def _batch_fetch_folder_relations(cr, folder_ids):
    write_groups = defaultdict(list)
    read_groups = defaultdict(list)
    tags_by_folder = defaultdict(list)

    if table_exists(cr, "documents_folder_res_groups_rel"):
        cr.execute(
            SQL(
                """SELECT documents_folder_id, res_groups_id
            FROM documents_folder_res_groups_rel
            WHERE documents_folder_id = ANY(%s)"""
            ),
            (list(folder_ids),),
        )
        for folder_id, group_id in cr.fetchall():
            write_groups[folder_id].append(group_id)

    if table_exists(cr, "documents_folder_read_groups"):
        cr.execute(
            SQL(
                """SELECT documents_folder_id, res_groups_id
            FROM documents_folder_read_groups
            WHERE documents_folder_id = ANY(%s)"""
            ),
            (list(folder_ids),),
        )
        for folder_id, group_id in cr.fetchall():
            read_groups[folder_id].append(group_id)

    if table_exists(cr, "documents_facet") and table_exists(cr, "documents_tag"):
        cr.execute(
            SQL(
                """SELECT f.folder_id, t.id
                FROM {} t JOIN {} f ON f.id = t.facet_id
                WHERE f.folder_id = ANY(%s)"""
            ).format(Identifier("documents_tag"), Identifier("documents_facet")),
            (list(folder_ids),),
        )
        for folder_id, tag_id in cr.fetchall():
            tags_by_folder[folder_id].append(tag_id)

    return write_groups, read_groups, tags_by_folder


def _fetch_folder_and_facet_names(cr, lang):
    folder_names = {}
    facet_details = {}
    # 1. Fetch Folder Names (Workspace)
    if table_exists(cr, "documents_folder"):
        cr.execute(
            SQL("SELECT id, name->>%s AS name FROM documents_folder"),
            (lang,),
        )
        folder_names = {f["id"]: f["name"].strip() for f in cr.dictfetchall()}
    # 2. Fetch Facet Details (Facet name and parent folder)
    if table_exists(cr, "documents_facet"):
        cr.execute(
            SQL("SELECT id, name->>%s AS name, folder_id FROM documents_facet"),
            (lang,),
        )
        facet_details = {
            f["id"]: {"name": f["name"].strip(), "folder_id": f["folder_id"]}
            for f in cr.dictfetchall()
        }

    return folder_names, facet_details


def migrate_documents_tags(cr, env, lang):
    """Migrate tags and facets from documents_tag to dms.tag and dms.category."""
    if not table_exists(cr, "documents_tag"):
        _logger.warning("Skipping tag migration: 'documents_tag' table does not exist.")
        return {}, {}

    _logger.info("Migrating tags from 'documents' to 'dms'...")

    DmsTag = env["dms.tag"]
    tag_mapping = {}

    # 1. Fetch Folder and Facet context data (Workspace and Facet names)
    folder_names, facet_details = _fetch_folder_and_facet_names(cr, lang)
    existing_tags = {_normalize(tag.name): tag for tag in DmsTag.search([])}
    cr.execute(
        SQL("SELECT id, name->>%s AS name, facet_id FROM {}").format(
            Identifier("documents_tag")
        ),
        (lang,),
    )
    old_tags = cr.dictfetchall()

    tags_to_create = []
    pending_keys = set()

    for old in old_tags:
        # build the full context name: [Workspace Name] > [Facet Name] > [Tag Name]
        facet = facet_details.get(old["facet_id"])
        # check the completeness of the context
        if (
            not facet
            or not facet.get("folder_id")
            or not folder_names.get(facet["folder_id"])
        ):
            # fallback: use tag name only
            full_name = old["name"].strip()
        else:
            folder_name = folder_names[facet["folder_id"]]
            facet_name = facet["name"]
            tag_name = old["name"].strip()
            full_name = f"{folder_name} > {facet_name} > {tag_name}"
        norm = _normalize(full_name)
        if not norm:
            continue
        if norm not in existing_tags and norm not in pending_keys:
            tags_to_create.append(
                {
                    "name": full_name,
                    "color": _default_color(),
                    "_old_id": old["id"],
                }
            )
            pending_keys.add(norm)
        record = existing_tags.get(norm)
        if record:
            tag_mapping[old["id"]] = record.id
    if tags_to_create:
        created = DmsTag.create(
            [
                {k: v for k, v in vals.items() if k not in ["_old_id", "category_id"]}
                for vals in tags_to_create
            ]
        )
        for vals, new_tag in zip(tags_to_create, created):
            norm = _normalize(new_tag.name)
            existing_tags[norm] = new_tag
            tag_mapping[vals["_old_id"]] = new_tag.id
    _logger.info("Migrated %d tags with full context.", len(tag_mapping))
    return tag_mapping, {}


def migrate_documents_folders(cr, env, lang, tag_mapping):
    """Migrate documents.folder to dms.directory, optimized for batch processing."""
    if not table_exists(cr, "documents_folder"):
        _logger.warning("Skipping folder migration: 'documents_folder' not found.")
        return {}

    _logger.info("Migrating folders from 'documents_folder' to 'dms_directory'...")

    cr.execute(
        SQL(
            """SELECT id, name->>%s AS name, parent_folder_id
            FROM {} ORDER BY parent_path"""
        ).format(Identifier("documents_folder")),
        (lang,),
    )
    folders = cr.dictfetchall()
    if not folders:
        _logger.info("No folders to migrate.")
        return {}

    DmsDirectory = env["dms.directory"]
    DmsAccessGroups = env["dms.access.group"]
    folder_mapping = {}
    storage = _get_or_create_default_storage(env)
    default_user_group_id = env.ref("base.group_user").id

    existing_dirs = DmsDirectory.search_read([], ["name", "parent_id"])
    existing_names_by_parent = defaultdict(set)
    for d in existing_dirs:
        parent_id = d["parent_id"][0] if d["parent_id"] else False
        existing_names_by_parent[parent_id].add(d["name"])

    folder_ids = [f["id"] for f in folders]
    write_groups, read_groups, tags_by_folder = _batch_fetch_folder_relations(
        cr, folder_ids
    )
    access_groups_to_create_vals = []
    dirs_to_update_tags = defaultdict(list)
    for folder in folders:
        try:
            parent_id = folder_mapping.get(folder["parent_folder_id"])
            names_in_parent = existing_names_by_parent[parent_id]
            vals = {
                "name": file_utils.unique_name_new(folder["name"], names_in_parent),
                "storage_id": storage.id if not parent_id else False,
                "parent_id": parent_id,
                "is_root_directory": not bool(parent_id),
            }

            new_dir = DmsDirectory.create(vals)
            names_in_parent.add(new_dir.name)
            folder_mapping[folder["id"]] = new_dir.id
            _logger.debug(
                "Created dms.directory: '%s' (ID: %s)", new_dir.name, new_dir.id
            )

            # Assign groups using pre-fetched data
            has_groups = False
            write_group_ids = write_groups.get(folder["id"], [])
            if write_group_ids:
                has_groups = True
                vals = {
                    "name": f"{new_dir.complete_name} Write Group",
                    "perm_create": True,
                    "perm_write": True,
                    "perm_unlink": True,
                    "group_ids": [Command.set(write_group_ids)],
                    "_dir_id": new_dir.id,
                }
                access_groups_to_create_vals.append(vals)
            read_group_ids = read_groups.get(folder["id"], [])
            if read_group_ids:
                has_groups = True
                vals = {
                    "name": f"{new_dir.complete_name} Read Group",
                    "group_ids": [Command.set(read_group_ids)],
                    "_dir_id": new_dir.id,
                }
                access_groups_to_create_vals.append(vals)
            # In case no group, directory will be invisible, so I decide to assign a new group
            # this group has full permision like no group in document folder
            if not has_groups:
                vals = {
                    "name": f"{new_dir.complete_name} Default Group",
                    "perm_create": True,
                    "perm_write": True,
                    "perm_unlink": True,
                    "group_ids": [Command.set([default_user_group_id])],
                    "_dir_id": new_dir.id,
                }
                access_groups_to_create_vals.append(vals)

            # Assign Tags
            folder_tag_ids = [
                tag_mapping[tag_id]
                for tag_id in tags_by_folder.get(folder["id"], [])
                if tag_id in tag_mapping
            ]
            if folder_tag_ids:
                dirs_to_update_tags[tuple(sorted(folder_tag_ids))].append(new_dir.id)

        except Exception:
            _logger.exception(
                "Error migrating folder ID %s (%s)", folder["id"], folder["name"]
            )

    for tag_ids_tuple, dir_ids in dirs_to_update_tags.items():
        DmsDirectory.browse(dir_ids).write(
            {"tag_ids": [Command.set(list(tag_ids_tuple))]}
        )

    if access_groups_to_create_vals:
        new_groups = DmsAccessGroups.create(
            [
                {k: v for k, v in vals.items() if k != "_dir_id"}
                for vals in access_groups_to_create_vals
            ]
        )

        dirs_to_update_groups = defaultdict(list)
        for vals, group in zip(access_groups_to_create_vals, new_groups):
            dirs_to_update_groups[vals["_dir_id"]].append(group.id)

        for dir_id, group_ids in dirs_to_update_groups.items():
            DmsDirectory.browse(dir_id).write({"group_ids": [Command.set(group_ids)]})

        # Recompute all user counts at once
        new_groups._compute_users()
    _logger.info("Successfully migrated %d folders.", len(folder_mapping))
    return folder_mapping


# flake8: noqa: C901
def migrate_documents_files(cr, env, folder_mapping, tag_mapping, batch_size):
    """Migrate documents.document to dms.file, optimized for batch processing."""
    if not table_exists(cr, "documents_document") or not folder_mapping:
        _logger.warning("Skipping file migration: table or folder mapping is missing.")
        return [], []

    _logger.info("Migrating files from 'documents_document' to 'dms_file'...")

    cr.execute(
        SQL("SELECT id FROM {} WHERE type = 'binary' ORDER BY id").format(
            Identifier("documents_document")
        )
    )
    all_doc_ids = [r[0] for r in cr.fetchall()]
    if not all_doc_ids:
        _logger.info("No documents to migrate.")
        return [], []

    DmsFile = env["dms.file"].with_context(bypass_check_size=True)
    created_file_ids, unmigrated_files = [], set()
    auto_commit = not getattr(threading.current_thread(), "testing", False)
    for i, batch_of_ids in enumerate(split_every(batch_size, all_doc_ids)):
        _logger.info("[Batch %d] Migrating %d documents...", i + 1, len(batch_of_ids))
        cr.execute(
            SQL(
                """SELECT id, name, folder_id, attachment_id, active
                FROM {} WHERE id = ANY(%s)"""
            ).format(Identifier("documents_document")),
            (list(batch_of_ids),),
        )
        documents = cr.dictfetchall()
        if not documents:
            continue

        directory_ids = list(
            {
                folder_mapping.get(doc["folder_id"])
                for doc in documents
                if doc.get("folder_id")
            }
        )
        existing_files = DmsFile.search_read(
            [("directory_id", "in", directory_ids)], ["name", "directory_id"]
        )
        existing_names_by_dir = defaultdict(set)
        for f in existing_files:
            existing_names_by_dir[f["directory_id"][0]].add(f["name"])

        # Batch-fetch tag relations for the current batch
        tags_by_doc = {}
        if table_exists(cr, "document_tag_rel"):
            cr.execute(
                SQL(
                    """SELECT documents_document_id, documents_tag_id
                    FROM {} WHERE documents_document_id = ANY(%s)"""
                ).format(Identifier("document_tag_rel")),
                (list(batch_of_ids),),
            )
            for doc_id, tag_id in cr.fetchall():
                if tag_id in tag_mapping:
                    tags_by_doc.setdefault(doc_id, []).append(tag_mapping[tag_id])

        attachment_ids = [
            doc["attachment_id"] for doc in documents if doc.get("attachment_id")
        ]
        attachment_data_map = {}
        if attachment_ids:
            cr.execute(
                SQL(
                    """
                    SELECT id, mimetype, file_size, checksum
                    FROM ir_attachment WHERE id = ANY(%s)"""
                ),
                (list(attachment_ids),),
            )
            attachment_data_map = {att["id"]: att for att in cr.dictfetchall()}

        files_to_create_vals = []
        batch_original_names = []
        for doc in documents:
            directory_id = folder_mapping.get(doc["folder_id"])
            if doc["folder_id"] and not directory_id:
                _logger.warning(
                    "Skipping doc %s: folder %s not found.", doc["id"], doc["folder_id"]
                )
                continue
            original_name = doc["name"]
            batch_original_names.append(original_name)
            sanitized_name, sanitized_ext = _preprocess_filename(original_name)
            names_in_directory = existing_names_by_dir[directory_id]
            unique_name = file_utils.unique_name_new(
                sanitized_name, names_in_directory, escape_suffix=True
            )
            attachment_id = doc.get("attachment_id")
            att_data = attachment_data_map.get(attachment_id)
            mimetype = att_data.get("mimetype") if att_data else None
            file_size = att_data.get("file_size") if att_data else 0
            checksum = att_data.get("checksum") if att_data else None
            extension_str = sanitized_ext[1:].strip().lower() if sanitized_ext else ""
            if not extension_str and mimetype:
                guessed_ext = mimetypes.guess_extension(mimetype)
                if guessed_ext:
                    extension_str = guessed_ext[1:].strip().lower()
            if not extension_str:
                extension_str = "bin"
            file_vals = {
                "name": unique_name,
                "directory_id": directory_id,
                "active": doc["active"],
                "attachment_id": attachment_id,
                "tag_ids": [Command.set(tags_by_doc.get(doc["id"], []))],
                "mimetype": mimetype,
                "size": file_size,
                "checksum": checksum,
                "extension": extension_str,
                "_original_name": original_name,
            }
            names_in_directory.add(file_vals["name"])
            files_to_create_vals.append(file_vals)

        if files_to_create_vals:
            create_payload = [
                {k: v for k, v in vals.items() if not k.startswith("_")}
                for vals in files_to_create_vals
            ]
            try:
                new_files = DmsFile.create(create_payload)
                created_file_ids.extend(new_files.ids)

                # Update attachments in bulk
                attachment_update_map = {}
                for vals, new_file in zip(files_to_create_vals, new_files):
                    if vals.get("attachment_id"):
                        attachment_update_map[vals["attachment_id"]] = new_file.id

                if attachment_update_map:
                    attachment_ids = list(attachment_update_map.keys())
                    case_clauses, params = [], []
                    for att_id, file_id in attachment_update_map.items():
                        case_clauses.append(SQL("WHEN %s THEN %s"))
                        params.extend([att_id, file_id])
                    params.append(tuple(attachment_ids))
                    query = SQL(
                        """
                        UPDATE ir_attachment
                        SET res_model = 'dms.file',
                            res_id = CASE id {cases} END
                        WHERE id IN %s
                    """
                    ).format(cases=SQL(" ").join(case_clauses))

                    cr.execute(query, params)
                    cr.execute("ANALYZE ir_attachment")

                if auto_commit:
                    env.cr.commit()
                    _logger.info("Committed batch %d.", i + 1)
            except Exception:
                _logger.exception("A critical error occurred during batch creation")
                if auto_commit:
                    env.cr.rollback()
                for name in batch_original_names:
                    _logger.error(
                        "Could not migrate file with original name: '%s'", name
                    )
                    unmigrated_files.add(name)

    _logger.info("Successfully migrated %d file records.", len(created_file_ids))
    return created_file_ids, list(unmigrated_files)


def merge_record_data(cr, env):
    xmlid_mapping = [
        ("dms.category_dms_security", "documents.module_category_documents_management"),
        ("dms.group_dms_user", "documents.group_documents_user"),
        ("dms.group_dms_manager", "documents.group_documents_manager"),
    ]
    for to_merge_xmlid, target_xmlid in xmlid_mapping:
        old_record = env.ref(to_merge_xmlid, raise_if_not_found=False)
        new_record = env.ref(target_xmlid, raise_if_not_found=False)
        if not old_record:
            _logger.warning("To merge XMLID not found: %s", to_merge_xmlid)
            continue
        if not new_record:
            _logger.warning("Target XMLID not found: %s", target_xmlid)
            continue
        try:
            openupgrade_merge_records.merge_records(
                env=env,
                model_name=new_record._name,
                record_ids=[old_record.id],
                target_record_id=new_record.id,
                method="orm",
            )
            openupgrade.rename_xmlids(
                cr,
                [
                    (target_xmlid, to_merge_xmlid),
                ],
            )
        except Exception as e:
            _logger.warning(
                "Error merging record from '%s' to '%s': %s",
                to_merge_xmlid,
                target_xmlid,
                e,
            )


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {"tracking_disable": True})
    if not openupgrade.is_module_installed(cr, "documents"):
        _logger.info("'documents' module not detected. Skipping migration.")
        return

    try:
        lang = get_lang(env).code or env.lang
        _logger.info(
            "Starting migration from 'documents' to 'dms' using lang '%s'", lang
        )
        merge_record_data(cr, env)
        tag_mapping, _ = migrate_documents_tags(cr, env, lang)
        folder_mapping = migrate_documents_folders(cr, env, lang, tag_mapping)
        BATCH_SIZE = models.INSERT_BATCH_SIZE
        _, failed_files = migrate_documents_files(
            cr, env, folder_mapping, tag_mapping, BATCH_SIZE
        )
        if failed_files:
            _logger.warning(
                "Migration completed with errors. %d files could not be migrated.",
                len(failed_files),
            )
        # Clear caches to avoid stale data issues
        _logger.info("Caches invalidated and registry cleared after migration.")
        env.invalidate_all()
        env.registry.clear_caches()
        _logger.info("Migration from 'documents' to 'dms' completed successfully.")
    except Exception:
        _logger.exception("Migration from 'documents' to 'dms' failed!")
        raise


def post_load_hook():
    @api.depends("mimetype", "content")
    def _compute_image_1920_new(self):
        """Provide thumbnail automatically if possible."""
        for one in self.filtered("mimetype"):
            if one.mimetype != "application/pdf" and one.mimetype in (
                *Image.MIME.values(),
                "image/svg+xml",
            ):
                # catch this error: https://github.com/odoo/odoo/blob/c27d978a/odoo/tools/image.py#L94
                # start hooks
                try:
                    File._compute_image_1920_origin(one)
                except (UserError, TypeError) as e:
                    _logger.warning(
                        "Failed to generate image_1920 for file %s (ID %s): %s",
                        one.name,
                        one.id,
                        str(e),
                    )
                    one.image_1920 = False
            else:
                one.image_1920 = False
                # end hooks

    if not hasattr(File, "_compute_image_1920_origin"):
        File._compute_image_1920_origin = File._compute_image_1920
    File._compute_image_1920 = _compute_image_1920_new


def uninstall_hook(cr, registry):
    _logger.info("Running uninstall_hook: cleaning up cloned tables...")
    env = api.Environment(cr, SUPERUSER_ID, {})
    modules = env["ir.module.module"].search(
        [
            ("name", "=", "documents"),
            ("state", "=", "installed"),
        ]
    )
    if modules:
        _logger.info("Triggering uninstall for: %s", "documents")
        constraint_to_drop = [
            ("documents_document", "documents_document_folder_id_fkey"),
        ]
        for table, constraint in constraint_to_drop:
            definition = sql.constraint_definition(cr, table, constraint)
            if definition:
                _logger.info(
                    "Dropping constraint %s on table %s: %s",
                    constraint,
                    table,
                    definition,
                )
                sql.drop_constraint(cr, table, constraint)
        modules.sudo().button_uninstall()
    else:
        _logger.info("No EE 'documents' modules currently installed.")
    _logger.info("Cleanup after uninstall completed.")
