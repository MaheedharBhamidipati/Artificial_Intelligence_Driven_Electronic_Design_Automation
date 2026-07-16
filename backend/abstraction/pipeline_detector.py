# ================================================================
# PIPELINE DETECTOR
# ================================================================

SEQUENTIAL_KEYWORDS = [

    "dff",
    "ff",
    "register",
    "reg",
    "latch"
]


def is_sequential(cell):

    ctype = str(
        cell.get("type", "")
    ).lower()

    for keyword in SEQUENTIAL_KEYWORDS:

        if keyword in ctype:

            return True

    return False


# ================================================================
# DETECT PIPELINES
# ================================================================

def detect_pipeline_structures(cells):

    sequential_cells = []

    for cell in cells:

        if is_sequential(cell):

            sequential_cells.append(cell)

    if len(sequential_cells) < 2:

        return []

    abstraction = {

        "type": "PIPELINE",

        "name": f"PIPELINE_{len(sequential_cells)}_STAGES",

        "stages": len(sequential_cells),

        "cells": sequential_cells
    }

    return [abstraction]