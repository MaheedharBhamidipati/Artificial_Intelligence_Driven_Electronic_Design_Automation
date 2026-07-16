"""
============================================================

AIDEA Semantic Detector

Author : AIDEA Project
Version : Phase 2.1

This is the module semantic_database.py's own docstring names
as the primary producer of a SemanticDatabase -- but the file
shipped empty. Without it, nothing in the pipeline actually
turns a loaded netlist into a populated SemanticDatabase, which
means CellIndex, LogicPass, RegisterPass, and FSMPass all have
no real entry point: every one of them requires a
SemanticDatabase to already exist and already be filled in.

SemanticDetector closes that gap. It is the bridge between:

    Yosys JSON / Design object  --->  SemanticDatabase

and it optionally drives the full semantic pass pipeline in
the correct order:

    1. Populate ports / cells / nets
    2. Build the CellIndex               (fast lookup cache)
    3. LogicPass       -> logic_type, clock/reset ports
    4. RegisterPass    -> register/pipeline/shift-register blocks
    5. FSMPass         -> FSM detection + state register info
    6. update_metrics()

============================================================
"""

from backend.semantic.semantic_database import (
    SemanticDatabase,
    Port,
    Net,
    SemanticCell,
)

from backend.semantic.index import CellIndex

from backend.semantic.passes import (
    LogicPass,
    RegisterPass,
    FSMPass,
)


class SemanticDetector:
    """
    Builds and analyzes a SemanticDatabase from netlist data.

    Two supported input shapes, so this stays usable whether or
    not the caller has backend.floorplanning's Design object
    available:

      * from_yosys_dict(yosys_json)  -- raw dict as produced by
        `yosys ... write_json`. Self-contained, no dependency on
        any other AIDEA package.

      * from_design(design)          -- duck-typed Design object
        (as returned by backend.floorplanning.netlist_loader
        .NetlistLoader.load()). Accepts anything with
        .top / .modules[*].ports / .cells / .nets, so it does
        NOT import backend.floorplanning directly and avoids a
        circular package dependency.
    """

    def __init__(self):

        self.db: SemanticDatabase = None

    # ======================================================
    # ENTRY POINT 1 -- RAW YOSYS JSON
    # ======================================================

    def from_yosys_dict(self, yosys_json: dict) -> SemanticDatabase:

        db = SemanticDatabase()

        modules = yosys_json.get("modules", {})

        if not modules:
            self.db = db
            return db

        # Yosys JSON top module: prefer one flagged as top,
        # otherwise fall back to the first module encountered.
        top_name = None

        for name, data in modules.items():

            attrs = data.get("attributes", {})

            if attrs.get("top") not in (None, 0, "0"):
                top_name = name
                break

        if top_name is None:
            top_name = next(iter(modules))

        db.design_name = top_name
        db.top_module = top_name

        module_data = modules[top_name]

        self._populate_ports(db, module_data)
        self._populate_cells(db, module_data)
        self._populate_nets(db, module_data)

        self.db = db
        return db

    # ======================================================
    # ENTRY POINT 2 -- Design OBJECT (duck-typed)
    # ======================================================

    def from_design(self, design, module_name: str = None) -> SemanticDatabase:
        """
        design: object with .top (str) and .modules (list of
        objects each with .name, .ports, .cells, .nets) --
        matches backend.floorplanning.design.Design /
        NetlistLoader output without importing that package.
        """

        db = SemanticDatabase()

        db.design_name = getattr(design, "top", "") or ""
        db.top_module = db.design_name

        target_name = module_name or db.top_module

        module = None

        for m in getattr(design, "modules", []):

            if getattr(m, "name", None) == target_name:
                module = m
                break

        if module is None and getattr(design, "modules", []):
            module = design.modules[0]
            db.top_module = getattr(module, "name", db.top_module)
            db.design_name = db.top_module

        if module is None:
            self.db = db
            return db

        for port in getattr(module, "ports", []):

            p = Port(
                name=port.name,
                direction=getattr(port, "direction", "input"),
                width=max(1, len(getattr(port, "bits", []) or [1])),
            )

            if p.direction == "output":
                db.add_output(p)
            else:
                db.add_input(p)

        for cell in getattr(module, "cells", []):

            db.add_cell(
                SemanticCell(
                    name=cell.name,
                    cell_type=getattr(cell, "cell_type", ""),
                    module=db.top_module,
                    attributes=dict(getattr(cell, "connections", {}) or {}),
                )
            )

        for net in getattr(module, "nets", []):

            db.add_net(Net(name=net.name))

        self.db = db
        return db

    # ======================================================
    # INTERNAL: YOSYS JSON PARSING HELPERS
    # ======================================================

    def _populate_ports(self, db, module_data):

        for pname, pdata in module_data.get("ports", {}).items():

            bits = pdata.get("bits", [])

            port = Port(
                name=pname,
                direction=pdata.get("direction", "input"),
                width=max(1, len(bits)) if bits else 1,
            )

            if port.direction == "output":
                db.add_output(port)
            else:
                db.add_input(port)

    def _populate_cells(self, db, module_data):

        for cname, cdata in module_data.get("cells", {}).items():

            db.add_cell(
                SemanticCell(
                    name=cname,
                    cell_type=cdata.get("type", ""),
                    module=db.top_module,
                    attributes=dict(cdata.get("parameters", {}) or {}),
                )
            )

    def _populate_nets(self, db, module_data):

        for nname, ndata in module_data.get("netnames", {}).items():

            db.add_net(Net(name=nname))

    # ======================================================
    # RUN FULL SEMANTIC PASS PIPELINE
    # ======================================================

    def analyze(self, db: SemanticDatabase = None) -> SemanticDatabase:
        """
        Runs CellIndex + LogicPass + FSMPass + RegisterPass in
        the order the individual passes actually require:

          1. LogicPass sets db.logic_type ("Combinational" /
             "Sequential" / "Mixed"), which FSMPass's first
             heuristic reads.
          2. FSMPass sets db.fsm.detected and db.fsm.* fields.
          3. RegisterPass runs last because
             RegisterPass.detect_state_register() only links
             db.fsm.state_register when db.fsm.detected is
             already True -- running RegisterPass before
             FSMPass (the naive order) makes that link silently
             never fire.

        Returns the populated database (also stored on self.db).
        """

        db = db or self.db

        if db is None:
            raise ValueError(
                "No SemanticDatabase available. Call "
                "from_yosys_dict() or from_design() first, or "
                "pass one explicitly to analyze()."
            )

        db.index = CellIndex()
        db.index.build(db.cells)

        LogicPass(db).run()
        FSMPass(db).run()
        RegisterPass(db).run()

        db.update_metrics()

        errors = db.validate()

        if errors:
            db.attributes["validation_warnings"] = errors

        self.db = db
        return db

    # ======================================================
    # CONVENIENCE ONE-SHOT ENTRY POINTS
    # ======================================================

    @classmethod
    def detect_from_yosys(cls, yosys_json: dict) -> SemanticDatabase:

        detector = cls()
        detector.from_yosys_dict(yosys_json)
        return detector.analyze()

    @classmethod
    def detect_from_design(cls, design, module_name: str = None) -> SemanticDatabase:

        detector = cls()
        detector.from_design(design, module_name=module_name)
        return detector.analyze()
