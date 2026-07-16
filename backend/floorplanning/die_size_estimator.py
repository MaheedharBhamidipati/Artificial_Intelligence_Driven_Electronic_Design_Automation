"""
=========================================================
AIDEA FLOORPLANNER

Die Size Estimator

Chip's width/height default to a hardcoded 100x100 (see
models.py) and nothing before this file ever replaced that
with something derived from the actual design -- every real
flow instead *sizes the die* from total cell area and a
target utilization before floorplanning starts, then treats
die/core dimensions as a solved-for quantity, not a constant.

Reuses MacroSizer's per-cell area model (macro_placer.py) as
the area basis, rather than inventing a second, inconsistent
unit-area constant: MacroSizer already turns "cell_count" into
a real macro footprint (UNIT_CELL_AREA * PADDING_FACTOR per
cell), and MacroPlacer will call it again later regardless, so
running it here first just makes that same number available
before placement instead of after. MacroSizer.size() is a pure
function of macro.cells (idempotent, no accumulated state), so
calling it twice across the pipeline is safe and cheap.

SOLVE:
    total_macro_area = sum(macro.width * macro.height)   [post-sizing]
    required_core_area = total_macro_area / utilization_target
    core_width  = sqrt(required_core_area * aspect_ratio)
    core_height = required_core_area / core_width
    die = core + 2 * core_margin on each axis

Deliberately NOT folding standard-cell area into this: this
codebase's data model doesn't carry a "cells not in any macro"
population (MacroBuilder groups every classified cell into
some macro), so there's no separate standard-cell count to add
without double-counting what MacroSizer already priced in.
=========================================================
"""

import math

from backend.floorplanning.macro_placer import MacroSizer


class DieSizeEstimator:

    def __init__(
        self,
        chip,
        utilization_target=0.65,
        aspect_ratio=1.0,
        core_margin=None,
        min_core_side=20.0,
    ):

        self.chip = chip

        # Clamped away from the extremes: 0 utilization is
        # undefined (division by zero) and >0.95 leaves no room
        # for the standard-cell region MacroLegalizer reserves
        # downstream.
        self.utilization_target = min(max(utilization_target, 0.05), 0.95)

        self.aspect_ratio = max(aspect_ratio, 0.1)

        # None means "leave chip.core_margin as whatever the
        # caller already set it to"; a real value overrides it
        # before the core/die math runs, since core_margin
        # directly determines die = core + 2*core_margin.
        self.core_margin = core_margin

        self.min_core_side = min_core_side

    # ------------------------------------------------------

    def _total_macro_area(self):

        MacroSizer().size(self.chip.macros)

        return sum(
            macro.width * macro.height
            for macro in self.chip.macros
        )

    # ------------------------------------------------------

    def plan(self):

        chip = self.chip

        if self.core_margin is not None:
            chip.core_margin = self.core_margin

        if not chip.macros:
            # Nothing to size against -- leave chip dimensions
            # exactly as the caller set them (degrade to a no-op,
            # same as every other stage here does on empty input).
            return chip

        total_macro_area = self._total_macro_area()

        if total_macro_area <= 0:
            return chip

        required_core_area = total_macro_area / self.utilization_target

        core_width = math.sqrt(required_core_area * self.aspect_ratio)

        core_height = required_core_area / core_width

        core_width = max(core_width, self.min_core_side)

        core_height = max(core_height, self.min_core_side)

        chip.width = round(core_width + 2 * chip.core_margin, 2)

        chip.height = round(core_height + 2 * chip.core_margin, 2)

        return chip
