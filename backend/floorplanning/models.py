from dataclasses import dataclass, field
from typing import List



# ==========================================================
# MACRO
# ==========================================================

@dataclass
class Macro:

    name: str

    macro_type: str

    x: float = 0

    y: float = 0

    width: float = 10

    height: float = 10

    # LEF/DEF ORIENT convention. N is the as-sized default
    # (identity orientation). Set by MacroOrientationOptimizer;
    # everything upstream of it just leaves this at "N".
    orientation: str = "N"

    # Set by PowerDomainManager; everything upstream leaves
    # this at None (single implicit domain).
    domain: str = None

    # Set by FloorplanConstraints when a fixed-coordinate
    # constraint targets this macro. Downstream stages that
    # reposition macros should treat fixed=True as a no-move
    # instruction; nothing upstream of FloorplanConstraints
    # currently reads this, since constraints apply last.
    fixed: bool = False

    cells: List[str] = field(default_factory=list)


# ==========================================================
# STANDARD CELL REGION
# ==========================================================

@dataclass
class StandardCellRegion:

    x: float

    y: float

    width: float

    height: float


# ==========================================================
# POWER PLANNING
# ==========================================================
#
# Rings, stripes and vias are kept as flat, independent
# geometric records (not a graph) on purpose: this mirrors
# how DEF SPECIALNETS represent a power grid -- a bag of
# rectangles/vias per net, not a connectivity model. Actual
# electrical connectivity is implied by physical overlap
# between same-net shapes, which is exactly what
# PGViaGenerator checks for when it decides where a via is
# legal.

@dataclass
class PowerRing:

    net: str            # "VDD" or "VSS"

    x: float

    y: float

    width: float

    height: float

    ring_width: float   # metal trace width of the ring frame

    layer: str = "M8"


@dataclass
class PowerStripe:

    net: str

    x: float

    y: float

    width: float

    height: float

    layer: str = "M6"

    @property
    def is_vertical(self):
        return self.height > self.width


@dataclass
class PGVia:

    net: str

    x: float

    y: float

    layer_from: str

    layer_to: str


@dataclass
class PowerPlan:

    rings: List[PowerRing] = field(default_factory=list)

    stripes: List[PowerStripe] = field(default_factory=list)

    vias: List[PGVia] = field(default_factory=list)

# ==========================================================
# POWER DOMAINS (multi-voltage)
# ==========================================================
#
# A PowerDomain's (x, y, width, height) is the bounding box
# of the macros assigned to it -- it is *derived* from macro
# placement, not planned independently the way rings/stripes
# are, since domain membership follows macro function
# (what voltage a block needs), not floorplan geometry.

@dataclass
class PowerDomain:

    name: str

    voltage: float

    x: float

    y: float

    width: float

    height: float

    macros: List[str] = field(default_factory=list)


@dataclass
class BoundaryCell:

    # "level_shifter" between domains at different voltages,
    # "isolation" between domains at the same voltage (e.g. an
    # always-on domain bordering a power-gateable one).
    kind: str

    x: float

    y: float

    from_domain: str

    to_domain: str


@dataclass
class PowerDomainPlan:

    domains: List[PowerDomain] = field(default_factory=list)

    boundary_cells: List[BoundaryCell] = field(default_factory=list)

# ==========================================================
# BLOCKAGES
# ==========================================================
#
# Placement and routing blockages are kept as two separate
# lists (not one generic "blockage" type) because they mean
# different things to different downstream tools: a
# placement blockage matters to a placer, a routing
# blockage matters to a router, and a real DEF file
# expresses them as distinct sections (PLACEMENT vs
# BLOCKAGE ... LAYER) for exactly that reason.

@dataclass
class PlacementBlockage:

    # "hard"   -- no macro or standard cell may be placed here
    # "soft"   -- placement discouraged but not illegal
    # "partial" -- placement allowed up to max_density
    kind: str

    x: float

    y: float

    width: float

    height: float

    max_density: float = 0.0   # only meaningful for kind == "partial"

    source: str = "manual"     # "manual" | "io_keepout" | "constraint"


@dataclass
class RoutingBlockage:

    layer: str

    x: float

    y: float

    width: float

    height: float

    source: str = "manual"     # "manual" | "macro_shadow"


@dataclass
class BlockagePlan:

    placement_blockages: List[PlacementBlockage] = field(default_factory=list)

    routing_blockages: List[RoutingBlockage] = field(default_factory=list)


# ==========================================================
# CONSTRAINTS
# ==========================================================
#
# A deliberately small, structured stand-in for what a real
# flow would pull from an SDC / floorplan-constraints file.
# Not an SDC parser -- these are plain Python objects the
# caller builds directly (or FloorplanConstraints.from_dicts
# builds from a JSON-like spec), covering the three
# constraint kinds floorplanning actually cares about at
# this stage: pinning a macro's coordinates, confining a set
# of macros to a region, and loosely grouping macros that
# should stay near each other.

@dataclass
class FixedMacroConstraint:

    macro_name: str

    x: float

    y: float


@dataclass
class RegionConstraint:

    name: str

    x: float

    y: float

    width: float

    height: float

    macro_names: List[str] = field(default_factory=list)


@dataclass
class GroupGuideConstraint:

    name: str

    macro_names: List[str] = field(default_factory=list)

    max_span: float = None     # optional soft-guide compliance check


# ==========================================================
# VALIDATION
# ==========================================================
#
# FloorplanValidator's output. A flat list of tagged issues
# (not per-category lists) so a caller that just wants
# "is this floorplan clean" can check is_clean without
# knowing the category taxonomy, while a caller that wants
# the detail can still filter by .category or .severity.

@dataclass
class ValidationIssue:

    severity: str    # "error" | "warning"

    category: str    # "macro_overlap" | "off_die" | "standard_cell_overlap"
                      # | "blockage" | "constraint" | "power_domain"

    message: str


@dataclass
class ValidationReport:

    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self):
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self):
        return [i for i in self.issues if i.severity == "warning"]

    @property
    def is_clean(self):
        return len(self.errors) == 0


# ==========================================================
# CONGESTION
# ==========================================================
#
# CongestionEstimator's output. A flat grid of bins (not a
# 2D array) for the same reason ValidationReport is a flat
# list: callers that just want "where are the hotspots" can
# filter CongestionMap.hotspots without knowing the grid
# indexing, while a renderer that wants the full grid still
# has grid_cols/grid_rows/bin_width/bin_height to reconstruct
# it.

@dataclass
class CongestionBin:

    x: float

    y: float

    width: float

    height: float

    # Routing demand estimated for this bin (RUDY-style,
    # area-weighted). Units are arbitrary but consistent with
    # supply below -- only their ratio (congestion) means
    # anything on its own.
    demand: float = 0.0

    # Routing supply left in this bin after routing blockages
    # and power-plan stripe occupancy are debited, summed
    # layer-by-layer (see congestion_estimator.py).
    supply: float = 0.0

    # demand / supply. >= 1.0 means this bin is asking for more
    # routing than the metal stack can offer here.
    congestion: float = 0.0

    hotspot: bool = False


@dataclass
class CongestionMap:

    bins: List[CongestionBin] = field(default_factory=list)

    grid_cols: int = 0

    grid_rows: int = 0

    bin_width: float = 0.0

    bin_height: float = 0.0

    @property
    def hotspots(self):
        return [b for b in self.bins if b.hotspot]

    @property
    def max_congestion(self):
        if not self.bins:
            return 0.0
        return max(b.congestion for b in self.bins)


# ==========================================================
# CHIP
# ==========================================================

# ==========================================================
# MACRO-LEVEL NET CONNECTIVITY
# ==========================================================
#
# Built by NetlistConnectivity from Design.modules[].nets +
# Cell.connections (the Yosys bit-id graph) once MacroBuilder
# has produced macros. A MacroNet is only recorded when a net
# actually spans 2+ macros -- a net whose fanout stays inside
# one macro's cell list has no effect on macro-level placement
# and would just be noise here. "weight" is the raw pin count
# on the net (a cheap proxy for how much that net should pull
# its macros together -- a bus with 32 pins wants its endpoints
# closer than a 1-bit control signal does).

@dataclass
class MacroNet:

    name: str

    # "clock" | "reset" | "data" -- cheap name-based heuristic,
    # see NetlistConnectivity._classify_net(). Downstream
    # consumers that need something more rigorous (real clock
    # tree synthesis) should treat this as a hint, not ground
    # truth.
    kind: str

    macros: List[str] = field(default_factory=list)

    weight: float = 1.0


@dataclass
class MacroNetlist:

    nets: List[MacroNet] = field(default_factory=list)

    @property
    def clock_nets(self):
        return [n for n in self.nets if n.kind == "clock"]

    @property
    def data_nets(self):
        return [n for n in self.nets if n.kind != "clock"]


# ==========================================================
# CLOCK REGIONS
# ==========================================================
#
# ClockRegionPlanner's output. One region per distinct clock
# net that reaches 2+ macros -- each region is the bounding
# box of the macros that net drives, which is the cheapest
# useful stand-in for "where a clock tree's leaves are" before
# real CTS exists. root_macro is a placement hint (the macro
# with the most cells on that clock net -- the closest thing
# this model has to "biggest sequential load"), not a real
# clock-source pin.

@dataclass
class ClockRegion:

    name: str

    clock_net: str

    x: float

    y: float

    width: float

    height: float

    macros: List[str] = field(default_factory=list)

    root_macro: str = None


@dataclass
class ClockPlan:

    regions: List[ClockRegion] = field(default_factory=list)

    # Clock nets that were detected but touch fewer than 2
    # macros (so no region was worth building) -- kept for
    # visibility/QoR reporting rather than silently dropped.
    unrouted_clock_nets: List[str] = field(default_factory=list)


@dataclass
class Chip:

    width: float = 100

    height: float = 100

    core_margin: float = 8

    io_margin: float = 5

    macros: List[Macro] = field(default_factory=list)

    standard_cells: StandardCellRegion = None

    power_plan: "PowerPlan" = None

    power_domain_plan: "PowerDomainPlan" = None

    blockage_plan: "BlockagePlan" = None

    congestion_map: "CongestionMap" = None

    # Set by NetlistConnectivity right after macros are built,
    # when a Design/Module with real net data is available.
    # None whenever FloorplanEngine is run cells-only (e.g.
    # test_floorplan.py's plain dict cells) -- every downstream
    # consumer (TimingDrivenFloorplanner, ClockRegionPlanner,
    # compute_metrics) must treat that as "no connectivity
    # info" and fall back to today's category-only behavior.
    macro_netlist: "MacroNetlist" = None

    clock_plan: "ClockPlan" = None

    constraint_violations: List[str] = field(default_factory=list)

    validation_report: "ValidationReport" = None


# ==========================================================
# FLOORPLAN RESULT
# ==========================================================

@dataclass
class FloorplanResult:

    chip: Chip

    utilization: float

    dead_space: float

    estimated_wirelength: float

    output_png: str

    output_json: str

    output_qor: str = None
    
    

@dataclass
class Port:

    name: str

    direction: str

    width: int = 1