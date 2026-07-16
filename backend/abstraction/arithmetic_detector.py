# ================================================================
# ARITHMETIC STRUCTURE DETECTOR
# ================================================================

import re


ARITHMETIC_KEYWORDS = [

    "add",
    "adder",
    "fa",
    "ha",
    "sub",
    "alu",
    "mul",
    "mac",
    "carry"
]


def is_arithmetic_cell(cell):

    ctype = str(
        cell.get("type", "")
    ).lower()

    cname = str(
        cell.get("name", "")
    ).lower()

    for keyword in ARITHMETIC_KEYWORDS:

        if keyword in ctype:

            return True

        if keyword in cname:

            return True

    return False


# ================================================================
# DETECT ARITHMETIC STRUCTURES
# ================================================================

def detect_arithmetic_structures(cells):

    arithmetic_cells = []

    for cell in cells:

        if is_arithmetic_cell(cell):

            arithmetic_cells.append(cell)

    if len(arithmetic_cells) == 0:

        return []

    # ============================================================
    # GROUP BY PREFIX
    # ============================================================

    grouped = {}

    for cell in arithmetic_cells:

        cname = str(
            cell.get("name", "")
        )

        prefix = re.sub(
            r'\d+$',
            '',
            cname
        )

        if prefix not in grouped:

            grouped[prefix] = []

        grouped[prefix].append(cell)

    abstractions = []

    for prefix, group in grouped.items():

        width = len(group)

        abstraction = {

            "type": "ARITHMETIC_CLUSTER",

            "subtype": "RCA",

            "name": f"{prefix.upper()}_{width}BIT",

            "width": width,

            "cells": group
        }

        abstractions.append(abstraction)

    return abstractions