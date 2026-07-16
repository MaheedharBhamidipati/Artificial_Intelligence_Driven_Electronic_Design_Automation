"""
=========================================================
AIDEA FLOORPLANNER

Power Plan Generator

Orchestrator for the PDN sub-flow -- the power-planning
equivalent of what FloorplanEngine.run() does for macro
placement. Runs, in order:

    PowerRingGenerator   -> VDD/VSS ring pair around the core
        |
        v
    PowerStripeGenerator -> V/H stripes, each net reaching
                             its own ring
        |
        v
    PGViaGenerator        -> stitches same-net stripe<->ring
                              and stripe<->stripe crossings

...and writes the result onto chip.power_plan. Runs
independently of macro placement/legalization -- the PDN
covers the whole core, macro-aware blockage keepouts are
placement_blockage_manager.py's job, not this file's.
=========================================================
"""

from backend.floorplanning.models import PowerPlan
from backend.floorplanning.power_ring_generator import PowerRingGenerator
from backend.floorplanning.power_stripe_generator import PowerStripeGenerator
from backend.floorplanning.pg_via_generator import PGViaGenerator


class PowerPlanGenerator:

    def __init__(
        self,
        chip,
        ring_width=2.0,
        ring_spacing=1.5,
        ring_margin=1.0,
        ring_layer="M8",
        stripe_pitch=10.0,
        stripe_width=1.0,
        stripe_layer="M6",
        nets=("VDD", "VSS"),
    ):

        self.chip = chip

        self.ring_generator = PowerRingGenerator(
            chip,
            ring_width=ring_width,
            ring_spacing=ring_spacing,
            ring_margin=ring_margin,
            layer=ring_layer,
            nets=nets,
        )

        self.stripe_pitch = stripe_pitch

        self.stripe_width = stripe_width

        self.stripe_layer = stripe_layer

    # ------------------------------------------------------

    def generate(self):

        rings = self.ring_generator.generate()

        stripe_generator = PowerStripeGenerator(
            self.chip,
            rings,
            pitch=self.stripe_pitch,
            stripe_width=self.stripe_width,
            layer=self.stripe_layer,
        )

        stripes = stripe_generator.generate()

        via_generator = PGViaGenerator(self.chip, rings, stripes)

        vias = via_generator.generate()

        self.chip.power_plan = PowerPlan(
            rings=rings,
            stripes=stripes,
            vias=vias,
        )

        return self.chip
