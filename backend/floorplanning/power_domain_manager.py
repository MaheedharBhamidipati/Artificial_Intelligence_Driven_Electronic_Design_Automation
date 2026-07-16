"""
=========================================================
AIDEA FLOORPLANNER

Power Domain Manager

Multi-voltage / power-domain planning, the pre-CTS step
real flows use to figure out where level shifters and
isolation cells need to go before UPF-driven place & route.

Two passes:

    1. ASSIGN -- every macro gets a domain, derived from its
       function via a voltage map (Memory macros run at a
       lower rail than IO pads, etc). Macros already sharing
       a voltage are folded into the same domain rather than
       kept as separate per-type domains, since that's what
       actually matters electrically -- two logic blocks on
       the same rail don't need a boundary cell between them
       even if MacroBuilder classified them differently.
       Each domain's region is the bounding box of its
       member macros post-legalization, NOT planned
       independently the way rings/stripes are.

    2. STITCH BOUNDARIES -- wherever two macros in DIFFERENT
       domains sit close enough to be physically adjacent,
       drop a boundary cell at the midpoint of the gap
       between them:
           - different voltage  -> level_shifter
           - same voltage       -> isolation
             (models an always-on domain bordering a
             power-gateable one at the same rail -- a real
             scenario UPF distinguishes even when the
             voltage numbers match)

Runs after MacroLegalizer (domain regions need real die
coordinates) and is independent of PowerPlanGenerator --
either can run first.
=========================================================
"""

from backend.floorplanning.models import PowerDomain, BoundaryCell, PowerDomainPlan


# Default voltage rail per macro category (volts). Purely a
# reasonable placeholder taxonomy -- callers with real UPF
# data should pass their own voltage_map.
DEFAULT_VOLTAGE_MAP = {
    "Memory": 0.72,
    "Arithmetic": 0.80,
    "Logic": 0.80,
    "Sequential": 0.80,
    "MUX": 0.80,
    "FSM": 0.80,
    "IO": 1.80,
    "Output": 1.80,
    "Unknown": 0.80,
}


class PowerDomainManager:

    def __init__(
        self,
        chip,
        voltage_map=None,
        adjacency_threshold=3.0,
    ):

        self.chip = chip

        self.voltage_map = voltage_map or DEFAULT_VOLTAGE_MAP

        self.adjacency_threshold = adjacency_threshold

    # ------------------------------------------------------
    # PASS 1: ASSIGN
    # ------------------------------------------------------

    def _voltage_for(self, macro):

        return self.voltage_map.get(
            macro.macro_type,
            self.voltage_map.get("Unknown", 0.80),
        )

    def _assign_domains(self):

        chip = self.chip

        by_voltage = {}

        for macro in chip.macros:

            voltage = self._voltage_for(macro)

            domain_name = f"PD_{voltage:.2f}V"

            macro.domain = domain_name

            by_voltage.setdefault(voltage, []).append(macro)

        domains = []

        for voltage, macros in sorted(by_voltage.items()):

            xs0 = [m.x for m in macros]

            ys0 = [m.y for m in macros]

            xs1 = [m.x + m.width for m in macros]

            ys1 = [m.y + m.height for m in macros]

            x0, y0 = min(xs0), min(ys0)

            x1, y1 = max(xs1), max(ys1)

            domains.append(
                PowerDomain(
                    name=f"PD_{voltage:.2f}V",
                    voltage=voltage,
                    x=round(x0, 3),
                    y=round(y0, 3),
                    width=round(x1 - x0, 3),
                    height=round(y1 - y0, 3),
                    macros=[m.name for m in macros],
                )
            )

        return domains

    # ------------------------------------------------------
    # PASS 2: BOUNDARY CELLS
    # ------------------------------------------------------

    @staticmethod
    def _gap(a, b):

        # Chebyshev-style separation between two axis-aligned
        # rects: 0 (or negative, i.e. overlapping) if they
        # touch/overlap along both axes, otherwise the actual
        # clearance along whichever axis separates them.
        dx = max(a.x - (b.x + b.width), b.x - (a.x + a.width), 0.0)

        dy = max(a.y - (b.y + b.height), b.y - (a.y + a.height), 0.0)

        return max(dx, dy)

    @staticmethod
    def _midpoint(a, b):

        ax, ay = a.x + a.width / 2, a.y + a.height / 2

        bx, by = b.x + b.width / 2, b.y + b.height / 2

        return (round((ax + bx) / 2, 3), round((ay + by) / 2, 3))

    def _detect_boundaries(self, domains_by_name):

        macros = self.chip.macros

        cells = []

        n = len(macros)

        for i in range(n):

            a = macros[i]

            for j in range(i + 1, n):

                b = macros[j]

                if a.domain == b.domain:
                    continue

                if self._gap(a, b) > self.adjacency_threshold:
                    continue

                voltage_a = domains_by_name[a.domain].voltage

                voltage_b = domains_by_name[b.domain].voltage

                kind = "level_shifter" if voltage_a != voltage_b else "isolation"

                x, y = self._midpoint(a, b)

                cells.append(
                    BoundaryCell(
                        kind=kind,
                        x=x,
                        y=y,
                        from_domain=a.domain,
                        to_domain=b.domain,
                    )
                )

        return cells

    # ------------------------------------------------------

    def generate(self):

        chip = self.chip

        if not chip.macros:

            chip.power_domain_plan = PowerDomainPlan(domains=[], boundary_cells=[])

            return chip

        domains = self._assign_domains()

        domains_by_name = {d.name: d for d in domains}

        boundary_cells = self._detect_boundaries(domains_by_name)

        chip.power_domain_plan = PowerDomainPlan(
            domains=domains,
            boundary_cells=boundary_cells,
        )

        return chip
