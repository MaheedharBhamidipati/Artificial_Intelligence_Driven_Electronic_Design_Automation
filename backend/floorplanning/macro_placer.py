"""
=========================================================
AIDEA FLOORPLANNER

Macro Placer

Replaces clustering.py's fixed row/column grid with an
actual optimization-driven placer, built on the same
representation Innovus / Fusion Compiler / Aprisa use
internally at this stage: a SEQUENCE PAIR.

A sequence pair (Gamma+, Gamma-) is a pair of permutations
of the macros. Given a pair, there is a well-defined,
overlap-free packing of rectangles it decodes to (Murata et
al., "VLSI Module Placement Based on Rectangle-Packing by
the Sequence-Pair", 1996). Searching over sequence pairs
with simulated annealing -- instead of searching over raw
(x, y) coordinates -- is what makes the search space finite,
discrete, and guaranteed-legal-by-construction: every
sequence pair decodes to a non-overlapping placement, so the
optimizer never has to fight overlap as a constraint, only
as an objective (bounding-box area / aspect ratio).

Pipeline position (replaces ClusterEngine):

    Macro Builder
        |
        v
    Macro Placer         <- this file (sizing + SA over sequence pairs)
        |
        v
    Macro Legalizer       <- snaps raw placer units into the real die
        |
        v
    Matplotlib Renderer

Wirelength note:
    MacroBuilder currently groups cells by *type* (Arithmetic,
    Sequential, ...), not by net connectivity between macro
    instances, so there is no macro-to-macro adjacency graph
    to route on yet. Until that exists (see: timing/congestion-
    aware follow-up), this placer's objective is bounding-box
    compaction + aspect-ratio matching, which is exactly what
    a real floorplanner optimizes before any net weights are
    available. `adjacency` is accepted as an optional argument
    so a future net-aware caller can drop in an HPWL term
    without changing this file's structure.
=========================================================
"""

import math
import random

from backend.floorplanning.models import Chip


# ==========================================================
# MACRO SIZING
# ==========================================================
# clustering.py / macro_builder.py both hardcoded every macro
# to 18x14 regardless of how many cells it actually contains.
# A macro with 400 cells and a macro with 4 cells were drawn
# the same size. Real floorplanners size a macro from its
# contained standard-cell area; we do the same, using a
# generic per-cell area placeholder (real units come later
# once LEF cell footprints are available) plus a padding
# factor for internal routing/pin overhead.
# ==========================================================

class MacroSizer:

    UNIT_CELL_AREA = 2.0

    PADDING_FACTOR = 1.35

    MIN_DIMENSION = 6.0

    DEFAULT_ASPECT = 1.15

    def size(self, macros):

        for macro in macros:

            cell_count = max(1, len(macro.cells))

            area = (
                cell_count
                * self.UNIT_CELL_AREA
                * self.PADDING_FACTOR
            )

            aspect = self.DEFAULT_ASPECT

            width = math.sqrt(area * aspect)

            height = area / width

            macro.width = round(max(self.MIN_DIMENSION, width), 2)

            macro.height = round(max(self.MIN_DIMENSION, height), 2)

        return macros


# ==========================================================
# SEQUENCE PAIR -> PACKING DECODER
# ==========================================================
# O(n^2) direct DP. Real tools use an O(n log n) LIS-based
# decode for hundreds of macros; at floorplan-stage macro
# counts (tens, not thousands) the O(n^2) version is simpler,
# exact, and fast enough per SA iteration.
# ==========================================================

def decode_sequence_pair(seq_plus, seq_minus, widths, heights, spacing=0.0):

    n = len(seq_plus)

    pos_plus = {idx: i for i, idx in enumerate(seq_plus)}

    pos_minus = {idx: i for i, idx in enumerate(seq_minus)}

    order = sorted(range(n), key=lambda idx: pos_plus[idx])

    x = {idx: 0.0 for idx in range(n)}

    y = {idx: 0.0 for idx in range(n)}

    for i, b in enumerate(order):

        for a in order[:i]:

            # same relative order in both sequences -> a is
            # left of b (horizontal constraint). `spacing` is a
            # routing-channel margin, not part of either macro's
            # reported footprint -- it only affects where the
            # *next* macro may start.
            if pos_minus[a] < pos_minus[b]:

                x[b] = max(x[b], x[a] + widths[a] + spacing)

            # order reversed between the two sequences -> a is
            # below b (vertical constraint)
            else:

                y[b] = max(y[b], y[a] + heights[a] + spacing)

    bbox_w = max(x[idx] + widths[idx] for idx in range(n)) if n else 0.0

    bbox_h = max(y[idx] + heights[idx] for idx in range(n)) if n else 0.0

    return x, y, bbox_w, bbox_h


# ==========================================================
# SIMULATED ANNEALING OVER SEQUENCE PAIRS
# ==========================================================

class SequencePairPlacer:

    def __init__(
        self,
        macros,
        target_aspect=1.0,
        iterations=None,
        seed=None,
        aspect_weight=0.35,
    ):

        self.macros = macros

        self.n = len(macros)

        self.widths = [m.width for m in macros]

        self.heights = [m.height for m in macros]

        self.target_aspect = target_aspect

        self.aspect_weight = aspect_weight

        avg_dim = (
            sum(self.widths) + sum(self.heights)
        ) / max(1, 2 * self.n)

        # Routing-channel spacing between macros, scaled to macro
        # size instead of a fixed absolute constant -- otherwise
        # this either vanishes (rounds to zero after legalization
        # scaling) for large designs or looks absurdly wide for
        # tiny ones.
        self.spacing = max(0.5, avg_dim * 0.2)

        # Scale annealing effort with problem size instead of a
        # single fixed constant -- a 4-macro design converges in
        # a couple hundred moves, a 40-macro design needs more.
        if iterations is None:
            iterations = max(500, 200 * self.n)

        self.iterations = iterations

        self.random = random.Random(seed)

    # ------------------------------------------------------

    def _cost(self, bbox_w, bbox_h):

        area = bbox_w * bbox_h

        if bbox_h == 0:
            return float("inf")

        aspect = bbox_w / bbox_h

        aspect_penalty = abs(aspect - self.target_aspect) * area

        return area + self.aspect_weight * aspect_penalty

    # ------------------------------------------------------
    # Perturbation moves. All three are the standard SP
    # neighborhood operators: swapping two macros' positions in
    # one or both permutations always yields another valid
    # sequence pair, so every neighbor is guaranteed legal.
    # ------------------------------------------------------

    def _perturb(self, seq_plus, seq_minus):

        if self.n < 2:
            return seq_plus, seq_minus

        seq_plus = list(seq_plus)

        seq_minus = list(seq_minus)

        move = self.random.random()

        i, j = self.random.sample(range(self.n), 2)

        if move < 0.34:

            seq_plus[i], seq_plus[j] = seq_plus[j], seq_plus[i]

        elif move < 0.67:

            seq_minus[i], seq_minus[j] = seq_minus[j], seq_minus[i]

        else:

            seq_plus[i], seq_plus[j] = seq_plus[j], seq_plus[i]

            seq_minus[i], seq_minus[j] = seq_minus[j], seq_minus[i]

        return seq_plus, seq_minus

    # ------------------------------------------------------

    def run(self):

        if self.n == 0:

            return {}, 0.0, 0.0, [], []

        if self.n == 1:

            return {0: (0.0, 0.0)}, self.widths[0], self.heights[0], [0], [0]

        seq_plus = list(range(self.n))

        seq_minus = list(range(self.n))

        self.random.shuffle(seq_plus)

        self.random.shuffle(seq_minus)

        x, y, bbox_w, bbox_h = decode_sequence_pair(
            seq_plus, seq_minus, self.widths, self.heights, self.spacing
        )

        best_cost = self._cost(bbox_w, bbox_h)

        best_state = (seq_plus, seq_minus, x, y, bbox_w, bbox_h)

        current_cost = best_cost

        temperature = max(best_cost * 0.05, 1.0)

        cooling_rate = 0.97

        moves_per_temp = max(10, self.n)

        while temperature > 1e-3 and self.iterations > 0:

            for _ in range(moves_per_temp):

                self.iterations -= 1

                cand_plus, cand_minus = self._perturb(seq_plus, seq_minus)

                cx, cy, cw, ch = decode_sequence_pair(
                    cand_plus, cand_minus, self.widths, self.heights, self.spacing
                )

                cand_cost = self._cost(cw, ch)

                delta = cand_cost - current_cost

                accept = delta < 0 or self.random.random() < math.exp(
                    -delta / temperature
                )

                if accept:

                    seq_plus, seq_minus = cand_plus, cand_minus

                    current_cost = cand_cost

                    if cand_cost < best_cost:

                        best_cost = cand_cost

                        best_state = (cand_plus, cand_minus, cx, cy, cw, ch)

                if self.iterations <= 0:
                    break

            temperature *= cooling_rate

        _, _, x, y, bbox_w, bbox_h = best_state

        positions = {idx: (x[idx], y[idx]) for idx in range(self.n)}

        winning_seq_plus, winning_seq_minus = best_state[0], best_state[1]

        return positions, bbox_w, bbox_h, winning_seq_plus, winning_seq_minus


# ==========================================================
# MACRO PLACER
# ==========================================================
# Drop-in replacement for ClusterEngine: same `.place(chip)`
# -> chip contract that FloorplanEngine already calls
# ClusterEngine.cluster() with, so floorplan_engine.py only
# needs an import + instantiation swap.
# ==========================================================

class MacroPlacer:

    def __init__(
        self,
        chip: Chip,
        iterations=None,
        seed=None,
    ):

        self.chip = chip

        self.iterations = iterations

        self.seed = seed

    def place(self):

        if not self.chip.macros:
            return self.chip

        MacroSizer().size(self.chip.macros)

        usable_w = max(1.0, self.chip.width - 2 * self.chip.core_margin)

        usable_h = max(1.0, self.chip.height - 2 * self.chip.core_margin)

        target_aspect = usable_w / usable_h

        sp = SequencePairPlacer(
            self.chip.macros,
            target_aspect=target_aspect,
            iterations=self.iterations,
            seed=self.seed,
        )

        positions, bbox_w, bbox_h, seq_plus, seq_minus = sp.run()

        for idx, macro in enumerate(self.chip.macros):

            raw_x, raw_y = positions[idx]

            macro.x = raw_x

            macro.y = raw_y

        # Stash the raw (unscaled) packing bbox AND the winning
        # sequence pair on the chip. MacroLegalizer only needs
        # the bbox (to scale into the die); MacroOrientationOptimizer
        # needs the sequence pair too, so it can re-decode the
        # SAME relative ordering with rotated macro dimensions
        # instead of re-solving placement from scratch.
        self.chip._raw_macro_bbox = (bbox_w, bbox_h)

        self.chip._raw_sequence_pair = (seq_plus, seq_minus)

        self.chip._macro_spacing = sp.spacing

        return self.chip
