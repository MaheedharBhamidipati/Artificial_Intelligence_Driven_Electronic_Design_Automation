"""
=========================================================
AIDEA Floorplanning

Macro Clustering Engine

Creates an initial textbook-style floorplan
from generic macros.

Future:
    Channel Detection
    Wirelength
    Congestion
    Placement Guidance
=========================================================
"""

from backend.floorplanning.models import (
    Chip,
    StandardCellRegion
)


class ClusterEngine:

    def __init__(self, chip: Chip):

        self.chip = chip

    # ==========================================================
    # SIMPLE CLUSTERING
    # ==========================================================

    def cluster(self):

        left_margin = 10
        top_margin = 82

        spacing_x = 6
        spacing_y = 8

        macro_width = 18
        macro_height = 14

        current_x = left_margin
        current_y = top_margin

        max_per_row = 4
        count = 0

        for macro in self.chip.macros:

            macro.width = macro_width
            macro.height = macro_height

            macro.x = current_x
            macro.y = current_y

            current_x += macro_width + spacing_x

            count += 1

            if count >= max_per_row:

                count = 0

                current_x = left_margin

                current_y -= macro_height + spacing_y

        # ------------------------------------------------------
        # Standard Cell Region
        # ------------------------------------------------------

        self.chip.standard_cells = StandardCellRegion(

            x=8,

            y=8,

            width=self.chip.width - 16,

            height=30

        )

        return self.chip