"""
=========================================================
AIDEA FLOORPLANNER

Power Ring Generator

Builds the VDD/VSS ring pair around the core, the way
Innovus's addRing does: two concentric metal frames, one
per net, nested inward from the core boundary with a fixed
spacing between them so they never short.

    core boundary
        |
        v
    [ VDD ring (outer) ]
        [ VSS ring (inner) ]
            [ usable placement area for stripes/macros ]

Each ring is stored as a single rectangle + ring_width
(the frame's trace width), not four separate segments --
that's sufficient to derive the frame's outer and inner
edges anywhere they're needed (stripe reach, via stitching)
without carrying four redundant records per ring.
=========================================================
"""

from backend.floorplanning.models import PowerRing


class PowerRingGenerator:

    def __init__(
        self,
        chip,
        ring_width=2.0,
        ring_spacing=1.5,
        ring_margin=1.0,
        layer="M8",
        nets=("VDD", "VSS"),
    ):

        self.chip = chip

        self.ring_width = ring_width

        self.ring_spacing = ring_spacing

        self.ring_margin = ring_margin

        self.layer = layer

        self.nets = nets

    # ------------------------------------------------------

    def generate(self):

        chip = self.chip

        core_x0 = chip.core_margin

        core_y0 = chip.core_margin

        core_w = max(1.0, chip.width - 2 * chip.core_margin)

        core_h = max(1.0, chip.height - 2 * chip.core_margin)

        rings = []

        for i, net in enumerate(self.nets):

            # Each successive ring nests inward from the one
            # before it by its own trace width plus a spacing
            # channel, so rings never touch or overlap.
            inset = self.ring_margin + i * (self.ring_width + self.ring_spacing)

            width = core_w - 2 * inset

            height = core_h - 2 * inset

            if width <= 0 or height <= 0:
                # Core too small for this many nested rings --
                # stop rather than emit a degenerate/negative
                # rectangle.
                break

            rings.append(
                PowerRing(
                    net=net,
                    x=round(core_x0 + inset, 3),
                    y=round(core_y0 + inset, 3),
                    width=round(width, 3),
                    height=round(height, 3),
                    ring_width=self.ring_width,
                    layer=self.layer,
                )
            )

        return rings

    # ------------------------------------------------------
    # Helpers used by the stripe/via generators to know where
    # a given ring's metal actually sits, without every caller
    # re-deriving inner/outer edges from (x, y, width, height,
    # ring_width) by hand.
    # ------------------------------------------------------

    @staticmethod
    def outer_bounds(ring: PowerRing):
        return (ring.x, ring.y, ring.x + ring.width, ring.y + ring.height)

    @staticmethod
    def inner_bounds(ring: PowerRing):
        return (
            ring.x + ring.ring_width,
            ring.y + ring.ring_width,
            ring.x + ring.width - ring.ring_width,
            ring.y + ring.height - ring.ring_width,
        )
