"""
==========================================================

AIDEA FLOORPLANNING ENGINE

Pipeline

Cells
   │
   ▼
Macro Builder
   │
   ▼
Macro Placer (sequence-pair simulated annealing)
   │
   ▼
Macro Legalizer (scale into die, grid-snap, std-cell region)
   │
   ▼
Matplotlib Renderer
   │
   ▼
Floorplan Result

NOTE: This used to run ClusterEngine, which laid every macro
out on a fixed row/column grid regardless of macro size or
count. clustering.py is kept in the package (still runnable
standalone / useful as a cheap fallback) but is no longer
what FloorplanEngine.run() calls. MacroPlacer + MacroLegalizer
replace it with an actual optimization-driven placement.

==========================================================
"""

import json
import os

from backend.floorplanning.models import (
    Chip,
    FloorplanResult,
    BlockagePlan
)

from backend.floorplanning.macro_builder import (
    MacroBuilder
)

from backend.floorplanning.netlist_connectivity import (
    NetlistConnectivity
)

from backend.floorplanning.timing_driven_floorplanner import (
    TimingDrivenFloorplanner
)

from backend.floorplanning.clock_region_planner import (
    ClockRegionPlanner
)

from backend.floorplanning.die_size_estimator import (
    DieSizeEstimator
)

from backend.floorplanning.macro_placer import (
    MacroPlacer
)

from backend.floorplanning.macro_orientation_optimizer import (
    MacroOrientationOptimizer
)

from backend.floorplanning.macro_legalizer import (
    MacroLegalizer
)

from backend.floorplanning.power_plan_generator import (
    PowerPlanGenerator
)

from backend.floorplanning.power_domain_manager import (
    PowerDomainManager
)

from backend.floorplanning.floorplan_constraints import (
    FloorplanConstraints
)

from backend.floorplanning.placement_blockage_manager import (
    PlacementBlockageManager
)

from backend.floorplanning.routing_blockage_manager import (
    RoutingBlockageManager
)

from backend.floorplanning.congestion_estimator import (
    CongestionEstimator
)

from backend.floorplanning.halo_keepout_generator import (
    HaloKeepoutGenerator
)

from backend.floorplanning.floorplan_qor_report import (
    FloorplanQorReport
)

from backend.floorplanning.floorplan_validator import (
    FloorplanValidator
)

from backend.floorplanning.renderers.matplotlib_renderer import (
    MatplotlibRenderer
)


class FloorplanEngine:

    def __init__(

        self,

        cells=None,

        semantic_database=None,

        output_directory="static/generated/floorplanning",

        constraints=None,

        extra_placement_blockages=None,

        # Optional backend.floorplanning.design.Module (or a
        # Design -- .top/.modules[0] is used automatically) that
        # supplies real net connectivity for the SAME cells
        # passed in cells= / semantic_database=. Cell names must
        # line up with this module's Cell.name entries, since
        # NetlistConnectivity joins macros to nets by cell name.
        # None (the default) preserves today's behavior exactly:
        # no chip.macro_netlist, no timing-driven refinement, no
        # clock regions -- category-only floorplanning.
        netlist_module=None
    ):

        self.db = semantic_database

        # Either FloorplanConstraints-model objects or plain
        # dicts (run through FloorplanConstraints.from_dicts
        # in run()) -- both are accepted so callers with real
        # SDC-derived structured data don't have to construct
        # model objects by hand.
        self.constraints = constraints or []

        self.extra_placement_blockages = extra_placement_blockages or []

        # A Design has .modules (list) + .top; a Module has
        # .cells/.nets directly. Accept either so callers can
        # pass whatever NetlistLoader.load() gave them without
        # having to reach into it themselves.
        if netlist_module is not None and hasattr(netlist_module, "modules"):

            module_by_name = {m.name: m for m in netlist_module.modules}

            netlist_module = module_by_name.get(
                netlist_module.top,
                netlist_module.modules[0] if netlist_module.modules else None,
            )

        self.netlist_module = netlist_module


        # ===========================================
        # Cell source of truth
        # ===========================================
        # semantic_database (a SemanticDatabase from the
        # semantic package) takes priority when provided;
        # otherwise fall back to a raw cells list. This used
        # to be immediately overwritten a few lines down by
        # an unconditional `self.cells = cells`, which wiped
        # out semantic_database.cells whenever a caller only
        # passed semantic_database= (cells defaults to None).
        # That bug is fixed by only setting self.cells once,
        # here.
        # ===========================================

        if semantic_database is not None:

            self.cells = semantic_database.cells

        else:

            self.cells = cells if cells else []

        # ===========================================
        # Default output folder
        # ===========================================

        if output_directory is None:

            project_root = os.path.abspath(
                os.path.join(
                    os.path.dirname(__file__),
                    "..",
                    ".."
                )
            )

            output_directory = os.path.join(
                project_root,
                "static",
                "generated",
                "floorplanning"
            )

        self.output_directory = output_directory

        os.makedirs(
            self.output_directory,
            exist_ok=True
        )
    # =====================================================

    def compute_metrics(self, chip):

        used_area = 0

        for macro in chip.macros:
            used_area += macro.width * macro.height

        total_area = chip.width * chip.height

        if total_area == 0:
            utilization = 0.0
        else:
            utilization = (used_area / total_area) * 100

        dead_space = max(0.0, 100.0 - utilization)

        # When real macro-level connectivity exists, use the
        # actual net-weighted half-perimeter wirelength instead
        # of the cell-count placeholder -- this is the whole
        # point of wiring connectivity through: a real
        # (if macro-granular) wirelength estimate instead of a
        # count-based stand-in.
        weighted_hpwl = TimingDrivenFloorplanner.estimate_weighted_hpwl(chip)

        if weighted_hpwl is not None:
            estimated_wirelength = weighted_hpwl
        else:
            # Phase 1 estimation (no connectivity available)
            estimated_wirelength = len(self.cells) * 5

        return (
            round(utilization, 2),
            round(dead_space, 2),
            estimated_wirelength
        )
    # =====================================================

    def export_json(

        self,

        chip,

        utilization,

        dead_space,

        wirelength,

        filename

    ):

        data = {

            "chip":{

                "width":chip.width,

                "height":chip.height

            },

            "macros":[],

            "utilization":utilization,

            "dead_space":dead_space,

            "estimated_wirelength":wirelength

        }

        for macro in chip.macros:

            data["macros"].append({

                "name":macro.name,

                "type":macro.macro_type,

                "x":macro.x,

                "y":macro.y,

                "width":macro.width,

                "height":macro.height,

                "orientation":macro.orientation,

                "domain":macro.domain,

                "cells":macro.cells

            })

        if chip.power_domain_plan is not None:

            data["power_domains"] = {

                "domains": [
                    {
                        "name": d.name,
                        "voltage": d.voltage,
                        "x": d.x,
                        "y": d.y,
                        "width": d.width,
                        "height": d.height,
                        "macros": d.macros,
                    }
                    for d in chip.power_domain_plan.domains
                ],

                "boundary_cells": [
                    {
                        "kind": c.kind,
                        "x": c.x,
                        "y": c.y,
                        "from_domain": c.from_domain,
                        "to_domain": c.to_domain,
                    }
                    for c in chip.power_domain_plan.boundary_cells
                ],
            }

        if chip.power_plan is not None:

            data["power_plan"] = {

                "rings": [
                    {
                        "net": r.net,
                        "x": r.x,
                        "y": r.y,
                        "width": r.width,
                        "height": r.height,
                        "ring_width": r.ring_width,
                        "layer": r.layer,
                    }
                    for r in chip.power_plan.rings
                ],

                "stripes": [
                    {
                        "net": s.net,
                        "x": s.x,
                        "y": s.y,
                        "width": s.width,
                        "height": s.height,
                        "layer": s.layer,
                    }
                    for s in chip.power_plan.stripes
                ],

                "vias": [
                    {
                        "net": v.net,
                        "x": v.x,
                        "y": v.y,
                        "layer_from": v.layer_from,
                        "layer_to": v.layer_to,
                    }
                    for v in chip.power_plan.vias
                ],
            }

        if chip.blockage_plan is not None:

            data["blockages"] = {

                "placement_blockages": [
                    {
                        "kind": b.kind,
                        "x": b.x,
                        "y": b.y,
                        "width": b.width,
                        "height": b.height,
                        "max_density": b.max_density,
                        "source": b.source,
                    }
                    for b in chip.blockage_plan.placement_blockages
                ],

                "routing_blockages": [
                    {
                        "layer": b.layer,
                        "x": b.x,
                        "y": b.y,
                        "width": b.width,
                        "height": b.height,
                        "source": b.source,
                    }
                    for b in chip.blockage_plan.routing_blockages
                ],
            }

        if chip.congestion_map is not None:

            data["congestion"] = {

                "grid_cols": chip.congestion_map.grid_cols,

                "grid_rows": chip.congestion_map.grid_rows,

                "bin_width": chip.congestion_map.bin_width,

                "bin_height": chip.congestion_map.bin_height,

                "max_congestion": chip.congestion_map.max_congestion,

                "bins": [
                    {
                        "x": b.x,
                        "y": b.y,
                        "width": b.width,
                        "height": b.height,
                        "demand": b.demand,
                        "supply": b.supply,
                        "congestion": b.congestion,
                        "hotspot": b.hotspot,
                    }
                    for b in chip.congestion_map.bins
                ],
            }

        if chip.macro_netlist is not None:

            data["macro_netlist"] = {

                "nets": [
                    {
                        "name": n.name,
                        "kind": n.kind,
                        "macros": n.macros,
                        "weight": n.weight,
                    }
                    for n in chip.macro_netlist.nets
                ],
            }

        if chip.clock_plan is not None:

            data["clock_plan"] = {

                "regions": [
                    {
                        "name": r.name,
                        "clock_net": r.clock_net,
                        "x": r.x,
                        "y": r.y,
                        "width": r.width,
                        "height": r.height,
                        "macros": r.macros,
                        "root_macro": r.root_macro,
                    }
                    for r in chip.clock_plan.regions
                ],

                "unrouted_clock_nets": chip.clock_plan.unrouted_clock_nets,
            }

        data["constraint_violations"] = chip.constraint_violations

        if chip.validation_report is not None:

            data["validation"] = {

                "is_clean": chip.validation_report.is_clean,

                "issues": [
                    {
                        "severity": issue.severity,
                        "category": issue.category,
                        "message": issue.message,
                    }
                    for issue in chip.validation_report.issues
                ],
            }

        with open(

            filename,

            "w",

            encoding="utf-8"

        ) as f:

            json.dump(

                data,

                f,

                indent=4

            )

    # =====================================================

    def run(self):

        chip = Chip()

        builder = MacroBuilder(

            self.cells

        )

        chip.macros = builder.build()

        # Real macro-level net connectivity, when a netlist
        # module was supplied -- joins macros to Design.nets via
        # Cell.connections bit ids (see netlist_connectivity.py).
        # None when netlist_module wasn't provided, which is the
        # correct "no connectivity info" signal every downstream
        # consumer below already checks for.
        if self.netlist_module is not None:

            chip.macro_netlist = NetlistConnectivity(
                self.netlist_module,
                chip.macros,
            ).build()

        # Sizes the die/core from actual cell area + a
        # utilization target instead of leaving chip.width/
        # height at Chip()'s hardcoded 100x100 default. Must run
        # before MacroPlacer: placer solves its aspect-ratio
        # objective against chip.width/height, so the die needs
        # real dimensions before placement, not after.
        chip = DieSizeEstimator(chip).plan()

        placer = MacroPlacer(

            chip

        )

        chip = placer.place()

        orientation_optimizer = MacroOrientationOptimizer(

            chip

        )

        chip = orientation_optimizer.optimize()

        legalizer = MacroLegalizer(

            chip

        )

        chip = legalizer.legalize()

        # Wirelength-driven refinement using real macro-net
        # connectivity, when available. Runs strictly after
        # legalize() (needs final, non-overlapping, in-core
        # macro geometry to nudge from) and strictly before
        # constraints (below), so a fixed-coordinate constraint
        # always has the final say -- same ordering rule the
        # existing constraints comment already documents.
        if chip.macro_netlist is not None and chip.macro_netlist.nets:

            chip = TimingDrivenFloorplanner(chip).optimize()

        # Runs last among the geometry-affecting stages, same
        # reason DEF fixed-placement overrides come after
        # placement: a constraint is allowed to override
        # wherever the optimizer decided to put a macro.
        if self.constraints:

            constraint_objs = self.constraints

            if isinstance(constraint_objs[0], dict):

                constraint_objs = FloorplanConstraints.from_dicts(constraint_objs)

            chip, _ = FloorplanConstraints(chip, constraint_objs).apply()

        blockage_manager = PlacementBlockageManager(

            chip,

            # Halo keepouts generated post-legalize (see
            # halo_keepout_generator.py's scope note: the placer
            # itself isn't halo-aware yet, so this is detection,
            # not prevention) plus whatever the caller supplied.
            extra_blockages=(
                HaloKeepoutGenerator(chip).generate()
                + self.extra_placement_blockages
            )

        )

        placement_blockages = blockage_manager.generate()

        chip.constraint_violations.extend(

            blockage_manager.check_violations(placement_blockages)

        )

        routing_blockages = RoutingBlockageManager(chip).generate()

        chip.blockage_plan = BlockagePlan(

            placement_blockages=placement_blockages,

            routing_blockages=routing_blockages

        )

        # Independent of PowerPlanGenerator -- domain regions
        # come from macro placement, not the PDN grid, so
        # either could run first.
        domain_manager = PowerDomainManager(

            chip

        )

        chip = domain_manager.generate()

        # Clock regions derived from final macro geometry +
        # clock-kind macro nets, same "runs after everything
        # that can still move a macro" placement as the domain
        # manager above. No-op (empty ClockPlan) without real
        # connectivity.
        chip.clock_plan = ClockRegionPlanner(chip).plan()

        # Runs against the finalized core geometry (post-legalize),
        # not the raw placer output -- rings/stripes need the real
        # die coordinates, not sequence-pair packing units.
        power_plan_generator = PowerPlanGenerator(

            chip

        )

        chip = power_plan_generator.generate()

        # Runs after blockages and the power plan are both on
        # chip -- congestion supply is debited by routing
        # blockages (macro shadow) and power-plan stripe
        # occupancy, so both need to already be populated.
        # Congestion itself still estimates demand from cell-
        # count density, not real net routes -- that's unrelated
        # to macro_netlist above (RUDY-style demand doesn't need
        # per-net routing, just density), so it's left as-is.
        chip.congestion_map = CongestionEstimator(chip).estimate()

        # Runs dead last: a full DRC-style re-check of the
        # finished chip, after every stage that can move a
        # macro or add a blockage/domain has already run.
        FloorplanValidator(chip).validate()

        (
            utilization,
            dead_space,
            wirelength
        ) = self.compute_metrics(chip)

        png_file = os.path.join(

            self.output_directory,

            "floorplan.png"

        )

        renderer = MatplotlibRenderer()

        renderer.render(

            chip,

            png_file

        )

        json_file = os.path.join(

            self.output_directory,

            "floorplan.json"

        )

        self.export_json(

            chip,

            utilization,

            dead_space,

            wirelength,

            json_file

        )

        qor_file = os.path.join(

            self.output_directory,

            "floorplan_qor.txt"

        )

        qor_report = FloorplanQorReport(

            chip,

            utilization,

            dead_space,

            wirelength

        )

        with open(qor_file, "w", encoding="utf-8") as f:

            f.write(qor_report.render_text())

        return FloorplanResult(

            chip=chip,

            utilization=utilization,

            dead_space=dead_space,

            estimated_wirelength=wirelength,

            output_png=png_file,

            output_json=json_file,

            output_qor=qor_file

        )