"""
=========================================================
AIDEA FLOORPLANNER

Congestion Estimator

Timing needs macro-level net connectivity that doesn't exist
in the data model yet (net/connection data is loaded by
NetlistLoader but never makes it into Chip or FloorplanEngine
-- see macro_placer.py's note on the same gap). Congestion
doesn't have that problem: a grid-based RUDY-style ("Rectangular
Uniform wire DensitY") density estimate can be grounded
entirely in geometry FloorplanEngine already produces --
macro placement + cell counts as a pin-density proxy, routing
blockages, and power-plan stripe occupancy per layer. No
netlist wiring required.

DEMAND (per bin):
    RUDY spreads each net's expected wiring uniformly across
    its bounding box. Without real macro-to-macro nets yet,
    that's approximated per-macro instead: each macro
    contributes routing demand proportional to its own cell
    count spread uniformly over its own footprint -- a macro
    with more cells packed into the same area implies more
    pins/connections needing to route out of that area. A
    bin under several overlapping macros sums their
    area-weighted contributions.

SUPPLY (per bin, per metal layer):
    Every layer in LAYER_STACK starts with the same flat
    per-area track capacity. Two things debit it, and only on
    the layer(s) they actually occupy:
      - routing blockages (macro shadow, M1-M3 by default)
      - power-plan stripes (M6 by default)
    Total bin supply sums the remaining capacity across all
    layers. This is deliberately layer-aware: summing blockage
    area directly against one shared supply number would mean
    a macro's 3-layer shadow zeroes out the *entire* stack's
    capacity instead of just those 3 layers out of N -- every
    macro-covered bin would trivially read as "over capacity",
    which isn't real signal. Debiting supply per-layer, and
    only on the layers actually blocked/occupied, avoids that.

CONGESTION (per bin):
    demand / supply, with supply floored at a small epsilon so
    a fully-zeroed stack doesn't divide by zero. A bin is a
    hotspot once that ratio reaches hotspot_threshold.
=========================================================
"""

from backend.floorplanning.models import CongestionBin, CongestionMap
from backend.floorplanning.utils import overlap_area


# Flat, uniform per-layer track capacity expressed as "supply
# units per unit area" -- arbitrary but consistent with the
# demand scale below (pin_density_scale); only their ratio is
# meaningful. Eight layers, M1 through M8, matching the layers
# already in play elsewhere in the flow (M1-M3 macro shadow in
# RoutingBlockageManager, M6 stripes / M8 rings in the PDN).
LAYER_STACK = ("M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8")

LAYER_CAPACITY = 1.0


class CongestionEstimator:

    def __init__(
        self,
        chip,
        grid_cols=10,
        grid_rows=10,
        pin_density_scale=1.0,
        hotspot_threshold=1.0,
    ):

        self.chip = chip

        self.grid_cols = max(1, grid_cols)

        self.grid_rows = max(1, grid_rows)

        self.pin_density_scale = pin_density_scale

        self.hotspot_threshold = hotspot_threshold

    # ------------------------------------------------------

    def _core_bounds(self):

        chip = self.chip

        x0 = chip.core_margin

        y0 = chip.core_margin

        x1 = chip.width - chip.core_margin

        y1 = chip.height - chip.core_margin

        return x0, y0, max(x1, x0), max(y1, y0)

    # ------------------------------------------------------

    def _make_bins(self):

        x0, y0, x1, y1 = self._core_bounds()

        bin_width = (x1 - x0) / self.grid_cols if x1 > x0 else 0.0

        bin_height = (y1 - y0) / self.grid_rows if y1 > y0 else 0.0

        bins = []

        for row in range(self.grid_rows):

            for col in range(self.grid_cols):

                bins.append(
                    CongestionBin(
                        x=round(x0 + col * bin_width, 3),
                        y=round(y0 + row * bin_height, 3),
                        width=round(bin_width, 3),
                        height=round(bin_height, 3),
                    )
                )

        return bins, bin_width, bin_height

    # ------------------------------------------------------
    # DEMAND
    # ------------------------------------------------------

    def _macro_demand(self, congestion_bin, macro):

        clipped = overlap_area(congestion_bin, macro)

        if clipped <= 0:
            return 0.0

        macro_area = macro.width * macro.height

        if macro_area <= 0:
            return 0.0

        pin_density = len(macro.cells) / macro_area

        return clipped * pin_density * self.pin_density_scale

    # ------------------------------------------------------

    def _demand(self, congestion_bin):

        return sum(
            self._macro_demand(congestion_bin, macro)
            for macro in self.chip.macros
        )

    # ------------------------------------------------------
    # SUPPLY
    # ------------------------------------------------------

    def _blocked_area_by_layer(self, congestion_bin):

        blocked = {layer: 0.0 for layer in LAYER_STACK}

        blockage_plan = getattr(self.chip, "blockage_plan", None)

        if blockage_plan is None:
            return blocked

        for blockage in blockage_plan.routing_blockages:

            if blockage.layer not in blocked:
                # Layer outside the modeled stack -- nothing to
                # debit here (LAYER_STACK is meant to cover the
                # full stack, but a caller-supplied blockage
                # could in principle name something else).
                continue

            blocked[blockage.layer] += overlap_area(congestion_bin, blockage)

        return blocked

    # ------------------------------------------------------

    def _stripe_occupied_area_by_layer(self, congestion_bin):

        occupied = {layer: 0.0 for layer in LAYER_STACK}

        power_plan = getattr(self.chip, "power_plan", None)

        if power_plan is None:
            return occupied

        for stripe in power_plan.stripes:

            if stripe.layer not in occupied:
                continue

            occupied[stripe.layer] += overlap_area(congestion_bin, stripe)

        return occupied

    # ------------------------------------------------------

    def _supply(self, congestion_bin):

        bin_area = congestion_bin.width * congestion_bin.height

        if bin_area <= 0:
            return 0.0

        blocked = self._blocked_area_by_layer(congestion_bin)

        occupied = self._stripe_occupied_area_by_layer(congestion_bin)

        supply = 0.0

        for layer in LAYER_STACK:

            # Each layer starts from the *same* bin_area (its
            # own full capacity), not from whatever's left of a
            # shared pool -- that's the layer-aware part. A
            # blockage named "M1" only ever touches this term,
            # never M4-M8's.
            remaining = bin_area

            remaining -= min(blocked[layer], bin_area)

            remaining -= min(occupied[layer], bin_area)

            supply += max(0.0, remaining) * LAYER_CAPACITY

        return supply

    # ------------------------------------------------------

    def estimate(self):

        bins, bin_width, bin_height = self._make_bins()

        for congestion_bin in bins:

            demand = self._demand(congestion_bin)

            supply = self._supply(congestion_bin)

            congestion_bin.demand = round(demand, 4)

            congestion_bin.supply = round(supply, 4)

            safe_supply = max(supply, 1e-6)

            ratio = demand / safe_supply

            congestion_bin.congestion = round(ratio, 4)

            congestion_bin.hotspot = ratio >= self.hotspot_threshold

        return CongestionMap(
            bins=bins,
            grid_cols=self.grid_cols,
            grid_rows=self.grid_rows,
            bin_width=round(bin_width, 3),
            bin_height=round(bin_height, 3),
        )
