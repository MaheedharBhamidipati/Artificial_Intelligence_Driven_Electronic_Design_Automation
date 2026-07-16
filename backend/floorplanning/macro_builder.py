"""
=========================================================
AIDEA FLOORPLANNER

Macro Builder

Uses Yosys synthesized cells.

Generic for

✔ Combinational
✔ Sequential
✔ FSM
✔ Hierarchical Designs
=========================================================
"""

from collections import defaultdict

from backend.floorplanning.models import Macro
from backend.floorplanning.macro_classifier import MacroClassifier


# ==========================================================
# CELL CLASSIFIER
# ==========================================================
# Classification itself now lives in macro_classifier.py so
# that MacroBuilder, MatplotlibRenderer, and utils.COLORS all
# share one taxonomy instead of drifting apart. This method is
# kept as a thin wrapper so existing callers of
# MacroBuilder(...).classify_cell(...) don't break.
# ==========================================================

class MacroBuilder:

    def __init__(self, cells):

        self.cells = cells

    # ------------------------------------------------------

    def classify_cell(self, cell_type):

        return MacroClassifier.classify(cell_type)

    # ==========================================================
    # BUILD MACROS
    # ==========================================================

    def build(self):

        grouped = defaultdict(list)

        # ------------------------------------------------------
        # Helper: works for dicts and Cell objects
        # ------------------------------------------------------

        def get_value(cell, key, default=None):

            if isinstance(cell, dict):
                return cell.get(key, default)

            if key == "type":
                return getattr(cell, "cell_type", default)

            return getattr(cell, key, default)

        # ------------------------------------------------------

        for cell in self.cells:

            macro_type = self.classify_cell(

                get_value(cell, "type", "")

            )

            grouped[macro_type].append(cell)

        macros = []

        x = 10
        y = 70

        spacing = 5

        width = 18
        height = 14

        for macro_type, cell_list in grouped.items():

            macro = Macro(

                name=f"{macro_type} Block",

                macro_type=macro_type,

                x=x,

                y=y,

                width=width,

                height=height,

                cells=[

                    get_value(c, "name", "")

                    for c in cell_list

                ]

            )

            macros.append(macro)

            x += width + spacing

            if x > 75:

                x = 10

                y -= height + spacing

        return macros