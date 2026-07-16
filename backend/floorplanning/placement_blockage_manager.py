"""
=========================================================
AIDEA FLOORPLANNER

Placement Blockage Manager

Owns two things:

    1. Generating the default hard placement blockage every
       real floorplan has even before a user adds their own:
       the io_margin band. Chip already carries io_margin as
       a number, but nothing before this file ever turned it
       into a placement-illegal region a macro could
       actually be checked against -- MacroLegalizer only
       ever reasoned about core_margin.

    2. Checking macros against ALL hard placement blockages
       (default + user-supplied via FloorplanConstraints /
       manual PlacementBlockage entries) and reporting
       violations. This mirrors what floorplan_validator.py
       will eventually do for overlap/off-die/etc checks --
       this file owns the blockage-specific slice of that so
       blockage violations are visible before a full
       validator exists.

Soft and partial blockages are recorded but not enforced
here (see PlacementBlockage docstring in models.py) -- a
"soft" blockage is a placer hint, "partial" is a density
cap; neither is a hard legality check the way "hard" is.
=========================================================
"""

from backend.floorplanning.models import PlacementBlockage
from backend.floorplanning.utils import overlap


class PlacementBlockageManager:

    def __init__(self, chip, extra_blockages=None, generate_io_keepout=True):

        self.chip = chip

        # Caller-supplied blockages (manual entries, or ones
        # FloorplanConstraints derived from RegionConstraints)
        # on top of whatever this manager generates itself.
        self.extra_blockages = list(extra_blockages or [])

        self.generate_io_keepout = generate_io_keepout

    # ------------------------------------------------------

    def _generate_io_keepout(self):

        chip = self.chip

        if chip.io_margin <= 0:
            return []

        # Four bands forming a frame between the die edge and
        # the core boundary -- the pad/IO ring area, where no
        # macro or standard cell placement is legal. Four
        # separate rectangles (not one frame record, unlike
        # PowerRing) because placement blockages are checked
        # via plain rectangle overlap, not ring inner/outer
        # band math -- four simple rects is simpler here, not
        # simpler *for* something, just simpler.
        outer_x0, outer_y0 = 0.0, 0.0

        outer_x1, outer_y1 = chip.width, chip.height

        inner_x0 = inner_y0 = chip.io_margin

        inner_x1 = chip.width - chip.io_margin

        inner_y1 = chip.height - chip.io_margin

        bands = [
            (outer_x0, outer_y0, outer_x1, inner_y0),  # bottom
            (outer_x0, inner_y1, outer_x1, outer_y1),  # top
            (outer_x0, outer_y0, inner_x0, outer_y1),  # left
            (inner_x1, outer_y0, outer_x1, outer_y1),  # right
        ]

        blockages = []

        for bx0, by0, bx1, by1 in bands:

            if bx1 <= bx0 or by1 <= by0:
                continue

            blockages.append(
                PlacementBlockage(
                    kind="hard",
                    x=round(bx0, 3),
                    y=round(by0, 3),
                    width=round(bx1 - bx0, 3),
                    height=round(by1 - by0, 3),
                    source="io_keepout",
                )
            )

        return blockages

    # ------------------------------------------------------

    def generate(self):

        blockages = []

        if self.generate_io_keepout:
            blockages.extend(self._generate_io_keepout())

        blockages.extend(self.extra_blockages)

        return blockages

    # ------------------------------------------------------

    def check_violations(self, blockages):

        violations = []

        hard_blockages = [b for b in blockages if b.kind == "hard"]

        for macro in self.chip.macros:

            for blockage in hard_blockages:

                if overlap(macro, blockage):

                    violations.append(
                        f"{macro.name} overlaps hard placement blockage "
                        f"({blockage.source}) at "
                        f"({blockage.x}, {blockage.y}, "
                        f"{blockage.width}x{blockage.height})"
                    )

        return violations
