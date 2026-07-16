"""
=========================================================
AIDEA FLOORPLANNER

Power Stripe Generator

Lays vertical and horizontal stripes across the core at a
fixed pitch, alternating net per stripe (the standard
"every other track is VDD/VSS" pattern real PDN generators
use).

GEOMETRY NOTE -- per-net reach:
    Naively stopping every stripe at a single shared inset
    (e.g. the core margin) is wrong here: PowerRingGenerator
    nests VSS *inside* VDD, so a shared inset either strands
    VDD stripes short of the VDD ring, or drives VSS stripes
    straight through/past the VDD ring band. Each stripe
    must instead span exactly to *its own net's* ring outer
    edge -- VDD stripes reach the (further out) VDD ring,
    VSS stripes reach the (further in) VSS ring -- so
    PGViaGenerator always has real same-net overlap to
    stitch a via at.
=========================================================
"""

from backend.floorplanning.models import PowerStripe
from backend.floorplanning.power_ring_generator import PowerRingGenerator


class PowerStripeGenerator:

    def __init__(
        self,
        chip,
        rings,
        pitch=10.0,
        stripe_width=1.0,
        layer="M6",
    ):

        self.chip = chip

        self.rings = rings

        self.pitch = pitch

        self.stripe_width = stripe_width

        self.layer = layer

        self.net_to_ring = {ring.net: ring for ring in rings}

    # ------------------------------------------------------

    def _net_for_index(self, i):

        nets = list(self.net_to_ring.keys())

        if not nets:
            return None

        return nets[i % len(nets)]

    # ------------------------------------------------------

    def _vertical_stripes(self):

        chip = self.chip

        stripes = []

        core_x0 = chip.core_margin

        core_x1 = chip.width - chip.core_margin

        if not self.rings:
            return stripes

        i = 0

        x = core_x0 + self.pitch

        while x < core_x1:

            net = self._net_for_index(i)

            ring = self.net_to_ring[net]

            # Span to this net's own ring, not a shared inset --
            # see module docstring.
            y0, y1 = ring.y, ring.y + ring.height

            stripes.append(
                PowerStripe(
                    net=net,
                    x=round(x - self.stripe_width / 2, 3),
                    y=round(y0, 3),
                    width=round(self.stripe_width, 3),
                    height=round(y1 - y0, 3),
                    layer=self.layer,
                )
            )

            x += self.pitch

            i += 1

        return stripes

    # ------------------------------------------------------

    def _horizontal_stripes(self):

        chip = self.chip

        stripes = []

        core_y0 = chip.core_margin

        core_y1 = chip.height - chip.core_margin

        if not self.rings:
            return stripes

        i = 0

        y = core_y0 + self.pitch

        while y < core_y1:

            net = self._net_for_index(i)

            ring = self.net_to_ring[net]

            x0, x1 = ring.x, ring.x + ring.width

            stripes.append(
                PowerStripe(
                    net=net,
                    x=round(x0, 3),
                    y=round(y - self.stripe_width / 2, 3),
                    width=round(x1 - x0, 3),
                    height=round(self.stripe_width, 3),
                    layer=self.layer,
                )
            )

            y += self.pitch

            i += 1

        return stripes

    # ------------------------------------------------------

    def generate(self):

        return self._vertical_stripes() + self._horizontal_stripes()
