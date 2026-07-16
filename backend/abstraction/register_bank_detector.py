# ================================================================
# REGISTER BANK DETECTOR
# ================================================================

REGISTER_KEYWORDS = [

    "dff",
    "ff",
    "register",
    "reg"
]


def is_register(cell):

    ctype = str(
        cell.get("type", "")
    ).lower()

    for keyword in REGISTER_KEYWORDS:

        if keyword in ctype:

            return True

    return False


# ================================================================
# DETECT REGISTER BANKS
# ================================================================

def detect_register_banks(cells):

    registers = []

    for cell in cells:

        if is_register(cell):

            registers.append(cell)

    if len(registers) < 4:

        return []

    abstraction = {

        "type": "REGISTER_BANK",

        "name": f"REGISTER_BANK_{len(registers)}",

        "width": len(registers),

        "cells": registers
    }

    return [abstraction]