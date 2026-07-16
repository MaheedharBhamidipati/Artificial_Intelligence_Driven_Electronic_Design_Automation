"""
=========================================================
AIDEA FLOORPLANNER

Timing-Driven Floorplanner

A post-legalization refinement pass: pulls macros that share
real netlist connectivity (chip.macro_netlist, built by
NetlistConnectivity) closer together, weighted by pin count on
each net -- the same intuition as a quadratic/analytic placer's
wirelength term, done cheaply at macro granularity instead of
full timing analysis (no real STA exists yet in this package).

Deliberately does NOT replace MacroLegalizer or reimplement its
scale-to-core / grid-snap machinery. It runs strictly after
legalize(): macros are already inside the core, already
grid-legal, already non-overlapping. This pass only nudges
macros toward their connectivity-weighted centroid a bounded
amount per iteration, then runs a small, self-contained
pairwise-separation sweep (push-apart-on-the-shallower-axis,
not MacroLegalizer's push-right-only sweep, since these nudges
can come from any direction) to restore non-overlap, and clamps
back inside the core band. No-op (returns chip unchanged) if
chip.macro_netlist is missing/empty, or if there's nothing to
refine (< 2 movable macros).
=========================================================
"""

from backend.floorplanning.utils import overlap


class TimingDrivenFloorplanner:

    def __init__(
        self,
        chip,
        iterations=25,
        step_fraction=0.22,
        macro_gap=1.0,
    ):

        self.chip = chip

        self.iterations = iterations

        # Fraction of the distance to the weighted centroid a
        # macro moves per iteration. Kept well under 1.0 so the
        # pass converges smoothly instead of overshooting and
        # bouncing macros against each other.
        self.step_fraction = step_fraction

        # Minimum clear space to maintain between macro edges,
        # matching the spirit of SequencePairPlacer's own
        # inter-macro spacing (see macro_placer.py) -- kept
        # separate here since this module doesn't import that
        # one.
        self.macro_gap = macro_gap

    # ------------------------------------------------------
    # Core / standard-cell band bounds to clamp into. Same
    # geometry MacroLegalizer already computed -- read it back
    # off chip rather than recomputing, since legalize() always
    # runs before this pass.
    # ------------------------------------------------------

    def _bounds(self):

        chip = self.chip

        x0 = chip.core_margin
        x1 = chip.width - chip.core_margin

        y1 = chip.height - chip.core_margin

        if chip.standard_cells is not None:
            # Macro band sits above the standard-cell band (see
            # MacroLegalizer._scale_to_core's band_gap comment).
            y0 = chip.standard_cells.y + chip.standard_cells.height + 1.0
        else:
            y0 = chip.core_margin

        if y0 >= y1:
            y0 = chip.core_margin

        return x0, y0, x1, y1

    # ------------------------------------------------------
    # Weighted-centroid target for each macro: average position
    # of every macro it shares a net with, weighted by that
    # net's pin count. A macro with no connectivity at all keeps
    # its current position as its own "target" (net force is
    # zero).
    # ------------------------------------------------------

    def _net_targets(self):

        macro_by_name = {m.name: m for m in self.chip.macros}

        targets = {name: [0.0, 0.0, 0.0] for name in macro_by_name}
        # targets[name] = [weighted_x_sum, weighted_y_sum, weight_sum]

        for net in self.chip.macro_netlist.nets:

            members = [macro_by_name[n] for n in net.macros if n in macro_by_name]

            if len(members) < 2:
                continue

            centers = [
                (m.x + m.width / 2.0, m.y + m.height / 2.0) for m in members
            ]

            for i, macro in enumerate(members):

                # Pull each macro toward the centroid of the
                # *other* macros on this net (excluding itself),
                # so a net doesn't just pull a macro toward its
                # own current position.
                others = centers[:i] + centers[i + 1:]

                if not others:
                    continue

                ox = sum(c[0] for c in others) / len(others)
                oy = sum(c[1] for c in others) / len(others)

                w = net.weight

                targets[macro.name][0] += ox * w
                targets[macro.name][1] += oy * w
                targets[macro.name][2] += w

        return targets

    # ------------------------------------------------------
    # One bounded step toward each macro's weighted target.
    # ------------------------------------------------------

    def _apply_step(self, targets):

        for macro in self.chip.macros:

            if macro.fixed:
                continue

            wx, wy, wsum = targets.get(macro.name, (0.0, 0.0, 0.0))

            if wsum <= 0.0:
                continue

            target_cx = wx / wsum
            target_cy = wy / wsum

            cur_cx = macro.x + macro.width / 2.0
            cur_cy = macro.y + macro.height / 2.0

            macro.x += (target_cx - cur_cx) * self.step_fraction
            macro.y += (target_cy - cur_cy) * self.step_fraction

    # ------------------------------------------------------
    # Pairwise separation sweep -- pushes overlapping macros
    # apart along whichever axis has the smaller overlap, which
    # (unlike MacroLegalizer's single push-right pass) works
    # correctly when the overlap came from an arbitrary-direction
    # nudge instead of grid-snap rounding.
    # ------------------------------------------------------

    def _resolve_overlaps(self):

        macros = [m for m in self.chip.macros if not m.fixed]

        for _ in range(12):

            any_overlap = False

            for i in range(len(macros)):

                for j in range(i + 1, len(macros)):

                    a, b = macros[i], macros[j]

                    if not overlap(a, b):
                        continue

                    any_overlap = True

                    overlap_x = min(a.x + a.width, b.x + b.width) - max(a.x, b.x)
                    overlap_y = min(a.y + a.height, b.y + b.height) - max(a.y, b.y)

                    if overlap_x <= overlap_y:

                        push = overlap_x / 2.0 + self.macro_gap / 2.0

                        if a.x <= b.x:
                            a.x -= push
                            b.x += push
                        else:
                            a.x += push
                            b.x -= push

                    else:

                        push = overlap_y / 2.0 + self.macro_gap / 2.0

                        if a.y <= b.y:
                            a.y -= push
                            b.y += push
                        else:
                            a.y += push
                            b.y -= push

            if not any_overlap:
                break

    # ------------------------------------------------------
    # Clamp every movable macro back inside the core/macro band.
    # ------------------------------------------------------

    def _clamp_to_bounds(self):

        x0, y0, x1, y1 = self._bounds()

        for macro in self.chip.macros:

            if macro.fixed:
                continue

            max_x = max(x0, x1 - macro.width)
            max_y = max(y0, y1 - macro.height)

            macro.x = min(max(macro.x, x0), max_x)
            macro.y = min(max(macro.y, y0), max_y)

    # ------------------------------------------------------

    def optimize(self):

        chip = self.chip

        netlist = getattr(chip, "macro_netlist", None)

        if netlist is None or not netlist.nets or len(chip.macros) < 2:
            return chip

        for macro in chip.macros:
            macro.x = round(macro.x, 6)
            macro.y = round(macro.y, 6)

        for _ in range(self.iterations):

            targets = self._net_targets()

            self._apply_step(targets)

            self._clamp_to_bounds()

            self._resolve_overlaps()

            self._clamp_to_bounds()

        for macro in chip.macros:
            macro.x = round(macro.x, 3)
            macro.y = round(macro.y, 3)

        return chip

    # ------------------------------------------------------
    # Weighted half-perimeter wirelength over macro_netlist --
    # used by FloorplanEngine.compute_metrics() in place of the
    # cell-count placeholder whenever real connectivity exists.
    # ------------------------------------------------------

    @staticmethod
    def estimate_weighted_hpwl(chip):

        netlist = getattr(chip, "macro_netlist", None)

        if netlist is None or not netlist.nets:
            return None

        macro_by_name = {m.name: m for m in chip.macros}

        total = 0.0

        for net in netlist.nets:

            members = [macro_by_name[n] for n in net.macros if n in macro_by_name]

            if len(members) < 2:
                continue

            xs = [m.x + m.width / 2.0 for m in members]
            ys = [m.y + m.height / 2.0 for m in members]

            hpwl = (max(xs) - min(xs)) + (max(ys) - min(ys))

            total += hpwl * net.weight

        return round(total, 3)
