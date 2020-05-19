# Copyright 2020 Antoni Romera
# Copyright 2017-2019 MuK IT GmbH
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import mimetypes
import os
import shutil
import tempfile

from odoo.tools.mimetypes import guess_mimetype


def check_name(name):
    tmp_dir = tempfile.mkdtemp()
    try:
        open(os.path.join(tmp_dir, name), "a").close()
    except IOError:
        return False
    finally:
        shutil.rmtree(tmp_dir)
    return True


def compute_name(name, suffix, escape_suffix):
    if escape_suffix:
        name, extension = os.path.splitext(name)
        return "{}({}){}".format(name, suffix, extension)
    else:
        return "{}({})".format(name, suffix)


def unique_name(name, names, escape_suffix=False):
    if name not in names:
        return name
    else:
        suffix = 1
        name = compute_name(name, suffix, escape_suffix)
        while name in names:
            suffix += 1
            name = compute_name(name, suffix, escape_suffix)
        return name


def guess_extension(filename=None, mimetype=None, binary=None):
    extension = filename and os.path.splitext(filename)[1][1:].strip().lower()
    if not extension and mimetype:
        extension = mimetypes.guess_extension(mimetype)[1:].strip().lower()
    if not extension and binary:
        mimetype = guess_mimetype(binary, default="")
        extension = mimetypes.guess_extension(mimetype)[1:].strip().lower()
    return extension
