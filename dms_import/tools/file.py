# Copyright 2025 Kencove (https://www.kencove.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import os
import re


def compute_name_new(name_part, suffix, ext_part):
    return "{}({}){}".format(name_part, suffix, ext_part)


def unique_name_new(name, names, escape_suffix=False):
    if name not in names:
        return name
    if escape_suffix:
        name_part, ext_part = os.path.splitext(name)
    else:
        name_part, ext_part = name, ""

    match = re.fullmatch(r"(.+)\((\d+)\)", name_part)
    if match:
        base_name_part = match.group(1).rstrip()
        suffix = int(match.group(2)) + 1
    else:
        base_name_part = name_part
        suffix = 1
    new_name = compute_name_new(base_name_part, suffix, ext_part)
    while new_name in names:
        suffix += 1
        new_name = compute_name_new(base_name_part, suffix, ext_part)

    return new_name
