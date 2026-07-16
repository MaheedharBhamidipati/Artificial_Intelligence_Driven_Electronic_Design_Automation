"""
============================================================

AIDEA Floorplanning Pipeline

This is the missing end-to-end glue for the RTL -> GDSII flow,
stage: Synthesis -> [ Semantic Detection -> Floorplanning ].

Before this file, the two packages could each run in
isolation (see test_loader.py, test_floorplan.py,
test_semantic_database.py) but nothing chained them together:

    Yosys JSON
        |
        v
    NetlistLoader.load()          <- backend.floorplanning
        |
        v
    (nothing wired this to SemanticDetector)
        |
        v
    SemanticDetector.analyze()    <- backend.semantic
        |
        v
    (FloorplanEngine accepted semantic_database=, but the
     cells assignment bug meant it never actually used it)
        |
        v
    FloorplanEngine.run()         <- backend.floorplanning

run_pipeline() below performs all four steps and returns the
same FloorplanResult FloorplanEngine.run() already produces,
plus the populated SemanticDatabase for anything downstream
(placement, timing, reports, AI explanations, etc.) that wants
richer semantic info than raw cells.

============================================================
"""

import json

from backend.floorplanning.netlist_loader import NetlistLoader
from backend.floorplanning.floorplan_engine import FloorplanEngine
from backend.floorplanning.models import FloorplanResult

try:
    from backend.semantic import SemanticDetector
except ImportError as e:  # pragma: no cover
    raise ImportError(
        "backend.semantic is required for the floorplanning "
        "pipeline (semantic detection runs before floorplanning "
        "in the RTL-to-GDSII flow). Make sure the semantic "
        "package is installed alongside floorplanning."
    ) from e


def run_pipeline(
    yosys_json_path: str,
    output_directory: str = None,
    module_name: str = None,
):
    """
    Full Synthesis-output -> Floorplan pipeline.

    yosys_json_path : path to the Yosys `write_json` output
                       for the synthesized design.
    output_directory : where floorplan.png / floorplan.json
                        get written. None uses FloorplanEngine's
                        default (static/generated/floorplanning).
    module_name : which module to floorplan, if the netlist has
                  more than one and you don't want the
                  auto-detected top.

    Returns: (FloorplanResult, SemanticDatabase)
    """

    # ------------------------------------------------------
    # 1. Load the synthesized netlist into the Design object
    # ------------------------------------------------------

    loader = NetlistLoader(yosys_json_path)
    design = loader.load()

    if not design.modules:
        raise ValueError(
            f"No modules found in netlist: {yosys_json_path}"
        )

    # ------------------------------------------------------
    # 2. Run semantic detection: Design -> SemanticDatabase
    #    (ports, cells, nets, logic type, clock/reset, FSM,
    #    register banks, ...)
    # ------------------------------------------------------

    detector = SemanticDetector()
    detector.from_design(design, module_name=module_name)
    db = detector.analyze()

    # ------------------------------------------------------
    # 3. Floorplan the design using the semantic database as
    #    the source of classified cells, plus the raw Design
    #    module for real macro-level net connectivity (see
    #    netlist_connectivity.py). SemanticDetector wraps the
    #    same underlying Cell objects/names Design.modules
    #    already has, so cell names line up for the connectivity
    #    join -- this only degrades gracefully (chip.macro_netlist
    #    stays None) if that ever stops being true for a given
    #    detector implementation.
    # ------------------------------------------------------

    module = None

    for candidate in design.modules:
        if candidate.name == (module_name or design.top):
            module = candidate
            break

    if module is None and design.modules:
        module = design.modules[0]

    engine = FloorplanEngine(
        semantic_database=db,
        output_directory=output_directory,
        netlist_module=module,
    )

    result: FloorplanResult = engine.run()

    return result, db


def run_pipeline_from_dict(
    yosys_json: dict,
    output_directory: str = None,
):
    """
    Same as run_pipeline(), but for callers that already have
    the Yosys JSON loaded in memory (e.g. streamed from a
    synthesis subprocess) instead of a file path. Uses
    SemanticDetector.from_yosys_dict() directly, so it does not
    require backend.floorplanning.design.Design at all.
    """

    detector = SemanticDetector()
    detector.from_yosys_dict(yosys_json)
    db = detector.analyze()

    engine = FloorplanEngine(
        semantic_database=db,
        output_directory=output_directory,
    )

    result: FloorplanResult = engine.run()

    return result, db


if __name__ == "__main__":

    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m backend.floorplanning.pipeline <netlist.json> [output_dir]")
        raise SystemExit(1)

    netlist_path = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else None

    result, db = run_pipeline(netlist_path, out_dir)

    print("=" * 60)
    print("AIDEA FLOORPLANNING PIPELINE COMPLETE")
    print("=" * 60)
    print("Top Module      :", db.top_module)
    print("Logic Type      :", db.logic_type)
    print("FSM Detected    :", db.fsm.detected)
    print("Cells           :", len(db.cells))
    print("Macros          :", len(result.chip.macros))
    print("Utilization     :", result.utilization, "%")
    print("Dead Space      :", result.dead_space, "%")
    print("Est. Wirelength :", result.estimated_wirelength)

    if result.chip.macro_netlist is not None:
        print("Macro Nets      :", len(result.chip.macro_netlist.nets))
        print("Clock Nets      :", len(result.chip.macro_netlist.clock_nets))

    if result.chip.clock_plan is not None:
        print("Clock Regions   :", len(result.chip.clock_plan.regions))

    print("PNG Output      :", result.output_png)
    print("JSON Output     :", result.output_json)
