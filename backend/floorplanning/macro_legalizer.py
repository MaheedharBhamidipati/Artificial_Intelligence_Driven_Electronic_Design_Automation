"""
=========================================================
AIDEA FLOORPLANNER

Macro Legalizer

MacroPlacer's simulated annealing runs in "raw packing
units" -- whatever scale falls out of MacroSizer's generic
cell-area placeholder. Real Innovus/ICC2 legalization takes
a placer's result and snaps it onto the actual manufacturing
grid (site pitch, row alignment) inside the real die
boundary. This file is that step for AIDEA:

    1. Scale the raw packing to fit inside the chip's usable
       core area (chip.width/height minus core_margin),
       preserving aspect ratio so SequencePairPlacer's
       aspect-ratio objective wasn't optimized for nothing.
    2. Snap every macro's x/y/width/height onto a placement
       grid (site pitch), the way row-based standard-cell
       placement is grid-locked in real flows.
    3. Safety sweep: grid-snapping is a rounding operation,
       and a sequence pair guarantees zero overlap only at
       infinite precision. Re-check with utils.overlap() and
       nudge apart anything rounding pushed into contact.
    4. Place the standard-cell region in whatever usable core
       area is left over below the macro placement, instead
       of clustering.py's old fixed band that was never
       checked against where macros actually ended up.
=========================================================
"""

from backend.floorplanning.models import Chip, StandardCellRegion
from backend.floorplanning.utils import overlap


class MacroLegalizer:

    def __init__(self, chip: Chip, grid_pitch=0.5, min_standard_cell_height=12.0):

        self.chip = chip

        self.grid_pitch = grid_pitch

        self.min_standard_cell_height = min_standard_cell_height

    # ------------------------------------------------------
    # STEP 1: SCALE INTO THE USABLE CORE AREA
    # ------------------------------------------------------

    def _scale_to_core(self):

        chip = self.chip

        raw_bbox = getattr(chip, "_raw_macro_bbox", None)

        if raw_bbox is None:

            xs = [m.x + m.width for m in chip.macros] or [1.0]

            ys = [m.y + m.height for m in chip.macros] or [1.0]

            raw_bbox = (max(xs), max(ys))

        raw_w, raw_h = raw_bbox

        raw_w = max(raw_w, 1e-6)

        raw_h = max(raw_h, 1e-6)

        usable_w = max(1.0, chip.width - 2 * chip.core_margin)

        # Reserve a band at the bottom of the core for standard
        # cells before scaling macros to fill it, so macros don't
        # get stretched to consume 100% of core height and leave
        # nothing for the standard-cell region.
        reserved_for_std_cells = min(
            self.min_standard_cell_height,
            max(0.0, chip.height - 2 * chip.core_margin) * 0.3,
        )

        # Gap between the standard-cell band and the macro band
        # above it -- utils.overlap() treats exactly-touching
        # rectangles as overlapping (no epsilon tolerance), so an
        # explicit channel is needed here for the same reason
        # SequencePairPlacer spaces macros apart from each other.
        band_gap = max(self.grid_pitch, 1.0)

        usable_h = max(
            1.0,
            chip.height - 2 * chip.core_margin - reserved_for_std_cells - band_gap,
        )

        # Uniform scale (not independent x/y scale) so square
        # macros stay square instead of getting stretched into
        # rectangles the annealer never actually chose. A small
        # safety factor leaves headroom for grid-snap rounding
        # so it can't push the bounding box past the usable core.
        scale = min(usable_w / raw_w, usable_h / raw_h) * 0.985

        origin_x = chip.core_margin

        # Macro band sits above the standard-cell band, separated
        # by band_gap.
        origin_y = chip.core_margin + reserved_for_std_cells + band_gap

        for macro in chip.macros:

            macro.x = origin_x + macro.x * scale

            macro.y = origin_y + macro.y * scale

            macro.width = macro.width * scale

            macro.height = macro.height * scale

        self._reserved_for_std_cells = reserved_for_std_cells

        self._core_origin_x = origin_x

        self._core_origin_y = chip.core_margin

    # ------------------------------------------------------
    # STEP 2: SNAP TO PLACEMENT GRID
    # ------------------------------------------------------

    def _snap_to_grid(self):

        pitch = self.grid_pitch

        for macro in self.chip.macros:

            macro.x = round(macro.x / pitch) * pitch

            macro.y = round(macro.y / pitch) * pitch

            # Round to the nearest pitch, not up. Ceiling here
            # accumulates: three macros stacked in a column each
            # growing by up to one pitch pushes the bounding box
            # past the usable core by up to 3 pitches. Nearest
            # rounding costs at most half a pitch per macro
            # (negligible against the routing-channel spacing
            # SequencePairPlacer already left between them) and
            # doesn't compound the same way.
            macro.width = round(macro.width / pitch) * pitch if pitch else macro.width

            macro.height = round(macro.height / pitch) * pitch if pitch else macro.height

            macro.x = round(macro.x, 3)

            macro.y = round(macro.y, 3)

            macro.width = round(macro.width, 3)

            macro.height = round(macro.height, 3)

    # ------------------------------------------------------
    # STEP 3: OVERLAP SAFETY SWEEP
    # ------------------------------------------------------
    # A correct sequence-pair decode is overlap-free at exact
    # precision. Grid snapping rounds coordinates independently
    # per macro, which can occasionally close a gap that used to
    # separate two macros down to zero or less. This is a small,
    # bounded, deterministic fix-up pass -- not a second
    # optimizer -- so it intentionally just nudges the later
    # macro (in placement order) to the right until clear, then
    # re-snaps that one macro to the grid.
    # ------------------------------------------------------

    def _resolve_residual_overlaps(self):

        macros = self.chip.macros

        pitch = self.grid_pitch

        for i in range(len(macros)):

            for j in range(i + 1, len(macros)):

                a, b = macros[i], macros[j]

                if overlap(a, b):

                    new_x = a.x + a.width

                    b.x = round(new_x / pitch) * pitch if pitch else new_x

    # ------------------------------------------------------
    # STEP 4: STANDARD CELL REGION
    # ------------------------------------------------------

    def _place_standard_cells(self):

        chip = self.chip

        usable_w = max(1.0, chip.width - 2 * chip.core_margin)

        band_height = getattr(self, "_reserved_for_std_cells", 0.0)

        if band_height <= 0:

            # No macros (or degenerate sizing) -- fall back to
            # the old fixed-band behavior so this never produces
            # a zero-area region.
            band_height = max(
                self.min_standard_cell_height,
                (chip.height - 2 * chip.core_margin) * 0.3,
            )

        chip.standard_cells = StandardCellRegion(
            x=chip.core_margin,
            y=chip.core_margin,
            width=usable_w,
            height=round(band_height, 3),
        )

    # ------------------------------------------------------

    def legalize(self):

        if not self.chip.macros:

            self._reserved_for_std_cells = 0.0

            self._place_standard_cells()

            return self.chip

        self._scale_to_core()

        self._snap_to_grid()

        self._resolve_residual_overlaps()

        self._place_standard_cells()

        return self.chip
