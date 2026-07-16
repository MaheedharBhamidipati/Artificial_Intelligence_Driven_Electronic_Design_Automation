"""
=========================================================
AIDEA FLOORPLANNER

Macro Classifier

Single source of truth for mapping a synthesized cell's
type string onto a floorplan macro category.

This used to live inline inside MacroBuilder.classify_cell().
Pulled out here because:

  1. utils.COLORS, MatplotlibRenderer, and MacroBuilder all
     need the SAME category names -- keeping the taxonomy in
     one place stops them drifting apart.
  2. The Semantic layer's CellIndex (backend/semantic/index/
     cell_index.py) classifies the same synthesized cells
     with a *finer* taxonomy (Comparator, Counter, Decoder,
     Shift Register, ...). Floorplanning intentionally uses
     a coarser bucket set, because macro-level floorplanning
     cares about placement-relevant categories, not full
     semantic detail. This module documents that mapping
     explicitly instead of leaving it implicit.

Category set (must stay in sync with floorplanning/utils.py
COLORS and MatplotlibRenderer's legend):

    Arithmetic, Sequential, Memory, MUX, FSM, IO, Logic

=========================================================
"""

from typing import Optional


# ==========================================================
# CATEGORY KEYWORD TABLE
# ==========================================================
# Order matters: first match wins. Arithmetic is checked
# before Sequential so e.g. an "ADDER_REG" style name still
# lands in Arithmetic, matching the original MacroBuilder
# behavior.
# ==========================================================

CATEGORY_KEYWORDS = {

    "Arithmetic": [
        "ADD", "SUB", "MUL", "DIV", "ALU", "FA", "HA", "ADDER", "MAC"
    ],

    "Sequential": [
        "DFF", "SDFF", "DFFE", "FDRE", "FDCE", "FDSE", "LATCH", "$DFF"
    ],

    "Memory": [
        "RAM", "ROM", "MEM", "FIFO", "SRAM"
    ],

    "MUX": [
        "MUX", "$MUX"
    ],

    "FSM": [
        "FSM", "STATE"
    ],

    "IO": [
        "INPUT", "OUTPUT", "IBUF", "OBUF"
    ],
}

DEFAULT_CATEGORY = "Logic"

VALID_CATEGORIES = list(CATEGORY_KEYWORDS.keys()) + [DEFAULT_CATEGORY]


class MacroClassifier:
    """
    Stateless classifier: given a raw cell_type string from the
    synthesized netlist (Yosys internal cell names like
    '$_DFF_P_', vendor primitives like 'FDRE', or semantic
    labels like 'RAM'), returns the floorplan macro category.
    """

    @staticmethod
    def classify(cell_type: Optional[str]) -> str:

        if not cell_type:
            return DEFAULT_CATEGORY

        t = str(cell_type).upper()

        for category, keywords in CATEGORY_KEYWORDS.items():

            for keyword in keywords:

                if keyword in t:
                    return category

        return DEFAULT_CATEGORY

    # ------------------------------------------------------
    # Batch helper: classify a whole cell list at once and
    # return {category: [cells...]} -- this is exactly the
    # grouping MacroBuilder.build() needs.
    # ------------------------------------------------------

    @staticmethod
    def group(cells, type_getter=None):
        """
        cells: iterable of dicts or Cell-like objects.
        type_getter: optional callable(cell) -> str. Defaults to
        handling both dicts (cell["type"]) and objects
        (cell.cell_type), matching MacroBuilder's existing
        get_value() helper.
        """

        from collections import defaultdict

        if type_getter is None:

            def type_getter(cell):
                if isinstance(cell, dict):
                    return cell.get("type", "")
                return getattr(cell, "cell_type", "")

        grouped = defaultdict(list)

        for cell in cells:
            category = MacroClassifier.classify(type_getter(cell))
            grouped[category].append(cell)

        return grouped
