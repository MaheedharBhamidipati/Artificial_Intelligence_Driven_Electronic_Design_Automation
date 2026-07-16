"""
============================================================

AIDEA Semantic Design Database

Author : AIDEA Project
Version : Phase 2.1

This module defines the common semantic database used by

    • Semantic Detector
    • Floorplanner
    • Placement
    • Routing
    • Timing
    • Power
    • Congestion
    • AI Assistant
    • Reports

Everything inside AIDEA should read/write this database.

============================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional


# ==========================================================
# PORT
# ==========================================================

@dataclass
class Port:

    name: str
    direction: str
    width: int = 1


# ==========================================================
# NET
# ==========================================================

@dataclass
class Net:

    name: str

    drivers: List[str] = field(default_factory=list)

    loads: List[str] = field(default_factory=list)


# ==========================================================
# CELL
# ==========================================================

@dataclass
class SemanticCell:

    name: str

    cell_type: str

    module: str = ""

    area: float = 0.0

    power: float = 0.0

    delay: float = 0.0

    inputs: List[str] = field(default_factory=list)

    outputs: List[str] = field(default_factory=list)

    attributes: Dict = field(default_factory=dict)


# ==========================================================
# BLOCK
# ==========================================================

@dataclass
class SemanticBlock:

    name: str

    block_type: str

    description: str = ""

    cells: List[SemanticCell] = field(default_factory=list)

    inputs: List[str] = field(default_factory=list)

    outputs: List[str] = field(default_factory=list)

    connections: List[str] = field(default_factory=list)

    area: float = 0.0

    power: float = 0.0

    delay: float = 0.0

    x: float = 0.0

    y: float = 0.0

    width: float = 0.0

    height: float = 0.0


# ==========================================================
# CONNECTION
# ==========================================================

@dataclass
class BlockConnection:

    source: str

    destination: str

    net_name: str

    weight: int = 1


# ==========================================================
# HIERARCHY NODE
# ==========================================================

@dataclass
class HierarchyNode:

    name: str

    module: str

    children: List["HierarchyNode"] = field(default_factory=list)


# ==========================================================
# FSM INFORMATION
# ==========================================================

@dataclass
class FSMInformation:
    """
    Stores all FSM-related semantic information.
    """

    # Detection
    detected: bool = False

    # FSM Characteristics
    machine_type: str = "Unknown"
    encoding: str = "Unknown"

    # Signals
    state_register: str = ""
    next_state_signal: str = ""
    output_logic: str = ""

    # State Information
    number_of_states: int = 0
    state_names: List[str] = field(default_factory=list)

    # Optional future extensions
    initial_state: str = ""
    current_state: str = ""
    transitions: List[dict] = field(default_factory=list)

# ==========================================================
# DESIGN METRICS
# ==========================================================

@dataclass
class DesignMetrics:

    gate_count: int = 0

    register_count: int = 0

    net_count: int = 0

    input_count: int = 0

    output_count: int = 0

    combinational_cells: int = 0

    sequential_cells: int = 0

    estimated_area: float = 0.0

    estimated_power: float = 0.0

    estimated_delay: float = 0.0

    utilization: float = 0.0

    estimated_wirelength: float = 0.0
    
    # ==========================================================
# SEMANTIC DATABASE
# ==========================================================

class SemanticDatabase:
    """
    Master Design Database

    Every AIDEA backend module should use this object instead
    of creating its own internal representation.
    """

    def __init__(self):

        # --------------------------------------------------
        # General Information
        # --------------------------------------------------

        self.design_name = ""

        self.top_module = ""

        self.logic_type = "Unknown"

        self.description = ""

        # --------------------------------------------------
        # Design Objects
        # --------------------------------------------------

        self.inputs: List[Port] = []

        self.outputs: List[Port] = []

        self.nets: List[Net] = []

        self.cells: List[SemanticCell] = []

        self.blocks: List[SemanticBlock] = []

        self.connections: List[BlockConnection] = []

        self.hierarchy: List[HierarchyNode] = []

        # --------------------------------------------------
        # FSM
        # --------------------------------------------------

        self.fsm = FSMInformation()

        # --------------------------------------------------
        # Metrics
        # --------------------------------------------------

        self.metrics = DesignMetrics()

        # --------------------------------------------------
        # Optional Metadata
        # --------------------------------------------------

        self.attributes = {}

    # ======================================================
    # ADD METHODS
    # ======================================================

    def add_input(self, port: Port):

        self.inputs.append(port)

    def add_output(self, port: Port):

        self.outputs.append(port)

    def add_cell(self, cell: SemanticCell):

        self.cells.append(cell)

    def add_net(self, net: Net):

        self.nets.append(net)

    def add_block(self, block: SemanticBlock):

        self.blocks.append(block)

    def add_connection(
        self,
        connection: BlockConnection
    ):

        self.connections.append(connection)

    def add_hierarchy(
        self,
        node: HierarchyNode
    ):

        self.hierarchy.append(node)

    # ======================================================
    # SEARCH METHODS
    # ======================================================

    def get_block(
        self,
        name: str
    ) -> Optional[SemanticBlock]:

        for block in self.blocks:

            if block.name == name:

                return block

        return None

    def get_cell(
        self,
        name: str
    ) -> Optional[SemanticCell]:

        for cell in self.cells:

            if cell.name == name:

                return cell

        return None

    def get_net(
        self,
        name: str
    ) -> Optional[Net]:

        for net in self.nets:

            if net.name == name:

                return net

        return None

    # ======================================================
    # COUNTS
    # ======================================================

    @property
    def number_of_blocks(self):

        return len(self.blocks)

    @property
    def number_of_cells(self):

        return len(self.cells)

    @property
    def number_of_nets(self):

        return len(self.nets)

    @property
    def number_of_inputs(self):

        return len(self.inputs)

    @property
    def number_of_outputs(self):

        return len(self.outputs)

    # ======================================================
    # BLOCK TYPES
    # ======================================================

    def blocks_by_type(
        self,
        block_type
    ):

        return [

            block

            for block in self.blocks

            if block.block_type == block_type

        ]
        
            # ======================================================
    # EXPORT
    # ======================================================

    def to_dict(self):

        return {

            "design_name": self.design_name,

            "top_module": self.top_module,

            "logic_type": self.logic_type,

            "description": self.description,

            "inputs": [

                asdict(x)

                for x in self.inputs

            ],

            "outputs": [

                asdict(x)

                for x in self.outputs

            ],

            "nets": [

                asdict(x)

                for x in self.nets

            ],

            "cells": [

                asdict(x)

                for x in self.cells

            ],

            "blocks": [

                asdict(x)

                for x in self.blocks

            ],

            "connections": [

                asdict(x)

                for x in self.connections

            ],

            "hierarchy": [

                asdict(x)

                for x in self.hierarchy

            ],

            "fsm": asdict(self.fsm),

            "metrics": asdict(self.metrics),

            "attributes": self.attributes

        }

    # ======================================================
    # SUMMARY
    # ======================================================

    def summary(self):

        print()

        print("=" * 60)

        print("AIDEA SEMANTIC DATABASE")

        print("=" * 60)

        print()

        print("Design :", self.design_name)

        print("Top    :", self.top_module)

        print("Logic  :", self.logic_type)

        print()

        print("Inputs :", len(self.inputs))

        print("Outputs:", len(self.outputs))

        print("Cells  :", len(self.cells))

        print("Blocks :", len(self.blocks))

        print("Nets   :", len(self.nets))

        print()

        print("FSM    :", self.fsm.detected)

        print()

        print("=" * 60)
        
        
         # ======================================================
    # SAVE DATABASE
    # ======================================================

    def save_json(
        self,
        filename
    ):

        import json

        with open(
            filename,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(

                self.to_dict(),

                f,

                indent=4

            )

    # ======================================================
    # UPDATE METRICS
    # ======================================================

    def update_metrics(self):

        self.metrics.input_count = len(self.inputs)

        self.metrics.output_count = len(self.outputs)

        self.metrics.gate_count = len(self.cells)

        self.metrics.net_count = len(self.nets)

        self.metrics.register_count = len(

            [

                c

                for c in self.cells

                if "DFF" in c.cell_type.upper()

            ]

        )

        self.metrics.sequential_cells = (

            self.metrics.register_count

        )

        self.metrics.combinational_cells = (

            self.metrics.gate_count -

            self.metrics.register_count

        )

    # ======================================================
    # CONNECTION GRAPH
    # ======================================================

    def build_connection_graph(self):

        graph = {}

        for block in self.blocks:

            graph[block.name] = []

        for conn in self.connections:

            if conn.source not in graph:

                graph[conn.source] = []

            graph[conn.source].append(

                conn.destination

            )

        return graph

    # ======================================================
    # BLOCK STATISTICS
    # ======================================================

    def block_statistics(self):

        stats = {}

        for block in self.blocks:

            stats[block.block_type] = (

                stats.get(

                    block.block_type,

                    0

                )

                + 1

            )

        return stats

    # ======================================================
    # VALIDATION
    # ======================================================

    def validate(self):

        errors = []

        if self.top_module == "":

            errors.append(

                "Top module not specified."

            )

        if len(self.inputs) == 0:

            errors.append(

                "No inputs detected."

            )

        if len(self.outputs) == 0:

            errors.append(

                "No outputs detected."

            )

        if len(self.cells) == 0:

            errors.append(

                "No synthesized cells."

            )

        return errors

    # ======================================================
    # STRING
    # ======================================================

    def __repr__(self):

        return (

            f"<SemanticDatabase "

            f"{self.top_module} "

            f"Cells={len(self.cells)} "

            f"Blocks={len(self.blocks)}>"

        )   
        
        