"""
=========================================================
AIDEA FLOORPLANNER

Halo Keepout Generator

A real hard macro carries a halo -- a margin around its
footprint where no *other* macro or standard cell may be
placed (routing congestion and macro-to-macro spacing rules
both depend on it). PlacementBlockageManager already generates
the io_margin keepout band, but nothing before this file turns
a macro's own footprint into a keepout for what's placed around
it -- MacroLegalizer only ever separates macros from each other
by a fixed band_gap, not a per-macro halo.

Built as four frame bands per macro (outer halo rect minus the
macro's own footprint), the same technique
PlacementBlockageManager._generate_io_keepout uses for the
die/core frame -- NOT one rectangle covering the halo *and* the
macro, which would make every macro trivially "violate" its own
halo blockage the moment PlacementBlockageManager.check_violations
checks it against itself.

EPSILON INSET: utils.overlap() treats exactly-touching rectangles
as overlapping (no tolerance -- see MacroLegalizer's own band_gap
comment for the same issue elsewhere in this pipeline). A frame
band's inner edge sitting exactly on the macro's boundary would
touch it, so every macro would register as violating its own halo
on every single run. A small INSET_EPSILON pulls each band's inner
edge back from the macro by a hair -- functionally still "halo
starts right at the macro edge" for any real placement check, but
no longer bitwise-touching the macro it belongs to.

SCOPE NOTE: like io_keepout, this generates halos *after*
placement/legalization already ran -- MacroLegalizer and
SequencePairPlacer are not halo-aware, so a halo violation here
is detected after the fact (as a constraint_violation), not
prevented during placement. Making the placer itself halo-aware
would mean feeding halo margins into MacroLegalizer's band_gap
spacing logic -- a placement-stage change, out of scope here.
=========================================================
"""

from backend.floorplanning.models import PlacementBlockage


# See module docstring's EPSILON INSET note.
INSET_EPSILON = 1e-3


class HaloKeepoutGenerator:

    def __init__(
        self,
        chip,
        halo_margin=2.0,
        per_macro_halo=None,
        kind="hard",
    ):

        self.chip = chip

        self.halo_margin = halo_margin

        # Optional {macro_name: margin} overrides for macros
        # that need a wider (or narrower, or zero via 0.0) halo
        # than the flat default -- e.g. a noisy analog macro
        # wanting extra isolation.
        self.per_macro_halo = per_macro_halo or {}

        self.kind = kind

    # ------------------------------------------------------

    def _halo_for(self, macro):

        return self.per_macro_halo.get(macro.name, self.halo_margin)

    # ------------------------------------------------------

    def _halo_bands(self, macro, halo):

        outer_x0 = macro.x - halo

        outer_y0 = macro.y - halo

        outer_x1 = macro.x + macro.width + halo

        outer_y1 = macro.y + macro.height + halo

        # Inset AWAY from the macro's own boundary (leaving a
        # hairline gap between band and macro) -- see module
        # docstring's EPSILON INSET note. Pulling inward instead
        # would carve a sliver *out of* the macro's own area and
        # still overlap it, which is the opposite of the fix.
        inner_x0 = macro.x - INSET_EPSILON

        inner_y0 = macro.y - INSET_EPSILON

        inner_x1 = macro.x + macro.width + INSET_EPSILON

        inner_y1 = macro.y + macro.height + INSET_EPSILON

        return [
            (outer_x0, outer_y0, outer_x1, inner_y0),   # bottom
            (outer_x0, inner_y1, outer_x1, outer_y1),   # top
            (outer_x0, inner_y0, inner_x0, inner_y1),   # left
            (inner_x1, inner_y0, outer_x1, inner_y1),   # right
        ]

    # ------------------------------------------------------

    def generate(self):

        blockages = []

        for macro in self.chip.macros:

            halo = self._halo_for(macro)

            if halo <= 0:
                continue

            for bx0, by0, bx1, by1 in self._halo_bands(macro, halo):

                if bx1 <= bx0 or by1 <= by0:
                    continue

                blockages.append(
                    PlacementBlockage(
                        kind=self.kind,
                        x=round(bx0, 3),
                        y=round(by0, 3),
                        width=round(bx1 - bx0, 3),
                        height=round(by1 - by0, 3),
                        source="macro_halo",
                    )
                )

        return blockages
