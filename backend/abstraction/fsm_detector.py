# ================================================================
# FSM DETECTOR
# ================================================================

FSM_KEYWORDS = [

    "state",
    "fsm",
    "next_state",
    "present_state"
]


def is_fsm_related(cell):

    cname = str(
        cell.get("name", "")
    ).lower()

    for keyword in FSM_KEYWORDS:

        if keyword in cname:

            return True

    return False


# ================================================================
# DETECT FSM STRUCTURES
# ================================================================

def detect_fsm_structures(cells):

    fsm_cells = []

    for cell in cells:

        if is_fsm_related(cell):

            fsm_cells.append(cell)

    if len(fsm_cells) == 0:

        return []

    abstraction = {

        "type": "FSM",

        "name": "FSM_CONTROLLER",

        "cells": fsm_cells
    }

    return [abstraction]