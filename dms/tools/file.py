# Copyright 2020 Antoni Romera
# Copyright 2017-2019 MuK IT GmbH
# Copyright 2024 Subteno - Timothée Vannier (https://www.subteno.com).
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import mimetypes
import os
import re
import shutil
import tempfile

from odoo.tools.mimetypes import guess_mimetype


def check_name(name):
    """
    Check if a file name is valid.

    :param str name: The file name to check.
    :return: True if the file name is valid, False otherwise.
    :rtype: bool
    """
    tmp_dir = tempfile.mkdtemp()
    try:
        open(os.path.join(tmp_dir, name), "a").close()
    except OSError:
        return False
    finally:
        shutil.rmtree(tmp_dir)
    return True


def compute_name(name, suffix, escape_suffix):
    """
    Compute a new name by adding a suffix to the original name.

    :param str name: The original name.
    :param int suffix: The suffix to add.
    :param bool escape_suffix: If True, the suffix is added in between the name and
    the file extension.
    :return: The new name.
    :rtype: str
    """
    if escape_suffix:
        name, extension = os.path.splitext(name)
        return f"{name}({suffix}){extension}"

    return f"{name}({suffix})"


def unique_name(name, names, escape_suffix=False):
    """
    Generate a unique name by adding a suffix to the original name.

    :param str name: The original name.
    :param list names: The list of existing names.
    :param bool escape_suffix: If True, the suffix is added in between the name and
    the file extension.
    :return: The unique name.
    :rtype: str
    """
    if name not in names:
        return name

    # Extract the suffix from the name
    # e.g: "file(1).txt" -> "1"
    #      "Directory (1)(2)" -> "2"
    digits = re.compile(r"\((\d+)\)(\.\w+)?$")
    match = digits.search(name)
    suffix = 1
    if match:
        suffix = int(match.group(1)) + 1
        # get the name without the suffix and append the extension
        name = name[: match.span()[0]] + (match.group(2) or "")

    name = compute_name(name, suffix, escape_suffix)
    while name in names:
        # has to check recursively if the new name is unique because the user can
        # rename the file with suffix n+1
        # and then duplicate the file n, leading to a new file with suffix n+1 which
        # is already used.
        return unique_name(name, names, escape_suffix)
    return name


def guess_extension(filename=None, mimetype=None, binary=None):
    """
    Guess the extension of a file.

    :param str filename: The name of the file.
    :param str mimetype: The mimetype of the file.
    :param str binary: The binary content of the file.

    :return: The extension of the file.
    :rtype: str
    """
    extension = filename and os.path.splitext(filename)[1][1:].strip().lower()
    if not extension and mimetype and mimetype != "application/x-empty":
        extension = mimetypes.guess_extension(mimetype)[1:].strip().lower()
    if not extension and binary:
        mimetype = guess_mimetype(binary, default="")
        extension = mimetypes.guess_extension(mimetype)[1:].strip().lower()
    return extension
