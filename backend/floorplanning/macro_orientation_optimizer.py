"""
=========================================================
AIDEA FLOORPLANNER

Macro Orientation Optimizer

Pipeline position (runs after MacroPlacer, before MacroLegalizer):

    Macro Builder
        |
        v
    Macro Placer              <- chooses WHERE each macro goes
        |
        v
    Macro Orientation Optimizer   <- this file: chooses HOW
        |                            each macro is rotated/mirrored
        v
    Macro Legalizer
        |
        v
    Matplotlib Renderer

WHY THIS IS A SEPARATE STAGE, NOT PART OF MacroPlacer:
    Real flows (Innovus/ICC2) do the same split: global macro
    placement first picks relative ordering to minimize
    bounding-box/wirelength, then orientation is resolved
    per-macro against that fixed ordering -- rotating a macro
    doesn't change which macros are to its left/right/above/
    below, only how much space it needs there. Reusing
    MacroPlacer's winning sequence pair (rather than
    re-solving placement from scratch) keeps that separation
    honest and avoids a second full annealing run over the
    combinatorially larger (sequence pair) x (orientation)
    joint space.

WHAT ORIENTATION ACTUALLY CHANGES HERE:
    LEF/DEF defines 8 orientations: N, S, E, W, FN, FS, FE, FW.
    Of those, only the 90-degree rotations (E, W, FE, FW) swap
    a macro's width and height -- the footprint any packer
    cares about. N vs S and FN vs FS are 180-degree rotations
    /mirrors that preserve the footprint exactly; they only
    change which edge a macro's pins face. AIDEA's macros don't
    carry pin geometry yet (that needs LEF pin data this
    project doesn't have), so there is no signal here to prefer
    N over S or FN over FS -- picking between them would be
    fake precision. This optimizer therefore searches the real
    degree of freedom (rotated vs. not) and reports it using
    the two orientation labels that are geometrically
    meaningful without pin data: "N" (as-sized) and "E" (rotated
    90 degrees). Extending to the full 8-way mirror set is a
    follow-up once macro_builder.py carries pin-side info.
=========================================================
"""

import math
import random

from backend.floorplanning.models import Chip
from backend.floorplanning.macro_placer import decode_sequence_pair


# Only these two are geometrically distinguishable without
# per-macro pin geometry (see module docstring). ROTATED maps
# to LEF orientation "E" (rotate 90 degrees), the standard
# choice for a rotated macro when the mirror axis is unknown.
UNROTATED_LABEL = "N"

ROTATED_LABEL = "E"


class MacroOrientationOptimizer:

    def __init__(
        self,
        chip: Chip,
        target_aspect=1.0,
        iterations=None,
        seed=None,
        aspect_weight=0.35,
    ):

        self.chip = chip

        self.target_aspect = target_aspect

        self.aspect_weight = aspect_weight

        n = len(chip.macros)

        if iterations is None:
            iterations = max(200, 60 * n)

        self.iterations = iterations

        self.random = random.Random(seed)

    # ------------------------------------------------------

    def _cost(self, bbox_w, bbox_h):

        if bbox_h == 0:
            return float("inf")

        area = bbox_w * bbox_h

        aspect = bbox_w / bbox_h

        aspect_penalty = abs(aspect - self.target_aspect) * area

        return area + self.aspect_weight * aspect_penalty

    # ------------------------------------------------------

    def optimize(self):

        chip = self.chip

        macros = chip.macros

        n = len(macros)

        if n == 0:
            return chip

        seq_pair = getattr(chip, "_raw_sequence_pair", None)

        if not seq_pair or not seq_pair[0]:

            # No sequence pair on the chip (e.g. MacroPlacer
            # wasn't run, or ran on a differently-ordered macro
            # list). Nothing safe to optimize against -- leave
            # every macro at its as-sized orientation rather
            # than guess at an ordering.
            return chip

        seq_plus, seq_minus = seq_pair

        spacing = getattr(chip, "_macro_spacing", 0.0)

        # Base (as-sized, "N") footprint for every macro, taken
        # from MacroPlacer's output. rotated[i] toggles between
        # (base_w, base_h) and the swapped (base_h, base_w).
        base_w = [m.width for m in macros]

        base_h = [m.height for m in macros]

        if n == 1:

            rotated = [False]

        else:

            rotated = [False] * n

        def dims_for(rotated_state):

            widths = [
                base_h[i] if rotated_state[i] else base_w[i]
                for i in range(n)
            ]

            heights = [
                base_w[i] if rotated_state[i] else base_h[i]
                for i in range(n)
            ]

            return widths, heights

        def cost_for(rotated_state):

            widths, heights = dims_for(rotated_state)

            _, _, bbox_w, bbox_h = decode_sequence_pair(
                seq_plus, seq_minus, widths, heights, spacing
            )

            return self._cost(bbox_w, bbox_h), bbox_w, bbox_h

        current_cost, _, _ = cost_for(rotated)

        best_rotated = list(rotated)

        best_cost = current_cost

        temperature = max(best_cost * 0.05, 1.0)

        cooling_rate = 0.95

        iterations_left = self.iterations

        # Only macros whose footprint isn't already square gain
        # anything from rotation -- skip them so the search
        # doesn't waste moves flipping a bit that can't change
        # the cost.
        rotatable = [i for i in range(n) if abs(base_w[i] - base_h[i]) > 1e-9]

        while temperature > 1e-3 and iterations_left > 0 and rotatable:

            for _ in range(max(5, len(rotatable))):

                iterations_left -= 1

                i = self.random.choice(rotatable)

                candidate = list(rotated)

                candidate[i] = not candidate[i]

                cand_cost, _, _ = cost_for(candidate)

                delta = cand_cost - current_cost

                accept = delta < 0 or self.random.random() < math.exp(
                    -delta / temperature
                )

                if accept:

                    rotated = candidate

                    current_cost = cand_cost

                    if cand_cost < best_cost:

                        best_cost = cand_cost

                        best_rotated = list(rotated)

                if iterations_left <= 0:
                    break

            temperature *= cooling_rate

        widths, heights = dims_for(best_rotated)

        x, y, bbox_w, bbox_h = decode_sequence_pair(
            seq_plus, seq_minus, widths, heights, spacing
        )

        for i, macro in enumerate(macros):

            macro.width = widths[i]

            macro.height = heights[i]

            macro.x = x[i]

            macro.y = y[i]

            macro.orientation = ROTATED_LABEL if best_rotated[i] else UNROTATED_LABEL

        # Keep MacroLegalizer's scale calculation honest -- it
        # reads chip._raw_macro_bbox, which is now stale if any
        # macro rotated.
        chip._raw_macro_bbox = (bbox_w, bbox_h)

        return chip
