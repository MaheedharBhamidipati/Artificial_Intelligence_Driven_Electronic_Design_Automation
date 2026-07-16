"""
=========================================================
AIDEA FLOORPLANNER

PG Via Generator

Rings sit on one layer (default M8), stripes on another
(default M6). A rectangle drawn on each layer isn't
electrically connected until something stitches them
together -- that's a via. This file finds every place a
stripe and something else *of the same net* physically
overlap and drops a via there:

    1. Stripe <-> its own net's ring, at the two points
       where the stripe actually crosses the ring's metal
       band (not the ring's full bounding box -- a ring is
       a frame, not a filled rectangle, so only the band
       within `ring_width` of each outer edge is real
       metal).
    2. Stripe <-> stripe, wherever a vertical and a
       horizontal stripe of the same net cross.

Different-net overlaps (e.g. a VDD stripe crossing over the
VSS ring) are intentionally skipped -- that's exactly the
short a real PDN via-stitch pass must NOT create.
=========================================================
"""

from backend.floorplanning.models import PGVia
from backend.floorplanning.power_ring_generator import PowerRingGenerator


class PGViaGenerator:

    def __init__(self, chip, rings, stripes):

        self.chip = chip

        self.rings = rings

        self.stripes = stripes

    # ------------------------------------------------------

    @staticmethod
    def _rect_overlap(ax0, ay0, ax1, ay1, bx0, by0, bx1, by1):

        ix0 = max(ax0, bx0)

        iy0 = max(ay0, by0)

        ix1 = min(ax1, bx1)

        iy1 = min(ay1, by1)

        if ix1 <= ix0 or iy1 <= iy0:
            return None

        return (ix0, iy0, ix1, iy1)

    # ------------------------------------------------------
    # STRIPE <-> RING
    # ------------------------------------------------------

    def _stripe_ring_vias(self):

        vias = []

        for ring in self.rings:

            ox0, oy0, ox1, oy1 = PowerRingGenerator.outer_bounds(ring)

            ix0, iy0, ix1, iy1 = PowerRingGenerator.inner_bounds(ring)

            # The ring's metal is the outer rectangle minus the
            # inner rectangle -- i.e. two horizontal bands (top,
            # bottom) and two vertical bands (left, right). A
            # stripe crossing the ring only makes real contact
            # within one of those four bands.
            bands = [
                (ox0, oy0, ox1, iy0),  # bottom band
                (ox0, iy1, ox1, oy1),  # top band
                (ox0, oy0, ix0, oy1),  # left band
                (ix1, oy0, ox1, oy1),  # right band
            ]

            for stripe in self.stripes:

                if stripe.net != ring.net:
                    continue

                sx0, sy0 = stripe.x, stripe.y

                sx1, sy1 = stripe.x + stripe.width, stripe.y + stripe.height

                for bx0, by0, bx1, by1 in bands:

                    hit = self._rect_overlap(sx0, sy0, sx1, sy1, bx0, by0, bx1, by1)

                    if hit is None:
                        continue

                    hx0, hy0, hx1, hy1 = hit

                    vias.append(
                        PGVia(
                            net=ring.net,
                            x=round((hx0 + hx1) / 2, 3),
                            y=round((hy0 + hy1) / 2, 3),
                            layer_from=stripe.layer,
                            layer_to=ring.layer,
                        )
                    )

        return vias

    # ------------------------------------------------------
    # STRIPE <-> STRIPE
    # ------------------------------------------------------

    def _stripe_stripe_vias(self):

        vias = []

        n = len(self.stripes)

        for i in range(n):

            a = self.stripes[i]

            for j in range(i + 1, n):

                b = self.stripes[j]

                if a.net != b.net:
                    continue

                if a.is_vertical == b.is_vertical:
                    # Two parallel stripes never form a real
                    # stitching via, and would produce a
                    # meaningless line-shaped "overlap" if they
                    # happened to share a pitch line.
                    continue

                hit = self._rect_overlap(
                    a.x, a.y, a.x + a.width, a.y + a.height,
                    b.x, b.y, b.x + b.width, b.y + b.height,
                )

                if hit is None:
                    continue

                hx0, hy0, hx1, hy1 = hit

                vias.append(
                    PGVia(
                        net=a.net,
                        x=round((hx0 + hx1) / 2, 3),
                        y=round((hy0 + hy1) / 2, 3),
                        layer_from=a.layer,
                        layer_to=b.layer,
                    )
                )

        return vias

    # ------------------------------------------------------

    def generate(self):

        return self._stripe_ring_vias() + self._stripe_stripe_vias()
