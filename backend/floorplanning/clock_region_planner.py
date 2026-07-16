"""
=========================================================
AIDEA FLOORPLANNER

Clock Region Planner

Groups macros into clock regions using chip.macro_netlist's
clock-kind nets (see netlist_connectivity.py's name-based
_classify_net heuristic). One ClockRegion per clock net that
reaches 2+ macros; the region's geometry is just the bounding
box of the macros that net drives -- the cheapest useful stand-
in for "where this clock's leaves physically sit" before real
clock-tree synthesis exists in this package.

Runs after macro geometry is final (post TimingDrivenFloor-
planner / constraints) and after PowerDomainManager, matching
the same "derived from final placement, not planned
independently" pattern PowerDomain regions already use (see
models.py's PowerDomain docstring).

No-op (returns an empty ClockPlan) if chip.macro_netlist is
missing or has no clock nets -- this is the expected case for
any chip run without real connectivity (cells-only callers like
test_floorplan.py).
=========================================================
"""

from backend.floorplanning.models import ClockPlan, ClockRegion


class ClockRegionPlanner:

    def __init__(self, chip):

        self.chip = chip

    # ------------------------------------------------------

    def plan(self):

        chip = self.chip

        netlist = getattr(chip, "macro_netlist", None)

        if netlist is None or not netlist.clock_nets:
            return ClockPlan(regions=[], unrouted_clock_nets=[])

        macro_by_name = {m.name: m for m in chip.macros}

        regions = []

        unrouted = []

        for idx, net in enumerate(netlist.clock_nets):

            members = [
                macro_by_name[name]
                for name in net.macros
                if name in macro_by_name
            ]

            if len(members) < 2:
                unrouted.append(net.name)
                continue

            x0 = min(m.x for m in members)
            y0 = min(m.y for m in members)
            x1 = max(m.x + m.width for m in members)
            y1 = max(m.y + m.height for m in members)

            # Root = macro carrying the most cells on this
            # clock net's macro set, i.e. the biggest sequential
            # load -- the closest thing available to "where the
            # clock tree would want to root" without real CTS.
            root = max(members, key=lambda m: len(m.cells))

            regions.append(
                ClockRegion(
                    name=f"CR_{idx}_{net.name}",
                    clock_net=net.name,
                    x=round(x0, 3),
                    y=round(y0, 3),
                    width=round(x1 - x0, 3),
                    height=round(y1 - y0, 3),
                    macros=[m.name for m in members],
                    root_macro=root.name,
                )
            )

        return ClockPlan(regions=regions, unrouted_clock_nets=unrouted)
