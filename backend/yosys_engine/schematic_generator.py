# ================================================================
# GENERIC RTL SCHEMATIC ENGINE
# ================================================================
# Author : V N S S S R Maheedhar
# Purpose:
#   Universal RTL schematic generator for:
#       - Sequential circuits
#       - Combinational circuits
#       - FSMs
#       - Pipelines
#       - Datapaths
#       - FPGA netlists
#       - ASIC RTL
#       - Hierarchical designs
#
# Features:
#   ✅ Hierarchy preservation
#   ✅ Smart clustering
#   ✅ Bus compression
#   ✅ Pipeline detection
#   ✅ FSM abstraction
#   ✅ Register bank abstraction
#   ✅ Carry chain grouping
#   ✅ Adaptive Graphviz layouts
#   ✅ Interactive SVG ready
#   ✅ Generic architecture
#   ✅ Huge graph optimization
#   ✅ Sequential + combinational support
#   ✅ DOT cleanup
#   ✅ Net filtering
#   ✅ Repeated instance compression
#   ✅ Auto styling engine
#   ✅ Layout heuristics
#
# ================================================================

from graphviz import Digraph
import re
import math
import json
import os
from collections import defaultdict
from collections import Counter
# ============================================================
# PHASE 3 — ABSTRACTION
# ============================================================

from backend.abstraction.arithmetic_detector import detect_arithmetic_structures
from backend.abstraction.pipeline_detector import detect_pipeline_structures
from backend.abstraction.fsm_detector import detect_fsm_structures
from backend.abstraction.register_bank_detector import detect_register_banks

from backend.abstraction.rtl_abstraction_engine import RTLAbstractionEngine

# ============================================================
# PHASE 4 — DATAPATH
# ============================================================

from backend.datapath.layer_builder import build_datapath_layers

from backend.datapath.datapath_engine import DatapathEngine
from backend.datapath.bus_router import GenericBusRouter
from backend.datapath.flow_router import RTLFlowRouter

# ============================================================
# PHASE 5 — AI ANALYSIS
# ============================================================

from backend.ai.hotspot_detector import detect_hotspots
from backend.ai.congestion_predictor import predict_congestion
from backend.ai.critical_path_estimator import estimate_critical_paths
from backend.ai.topology_optimizer import optimize_topology

from backend.ai.rtl_analyzer_ai import AIRTLAnalyzer

# ============================================================
# PHASE 6
# ============================================================

from backend.interactive.hierarchy_explorer import HierarchyExplorer
from backend.interactive.semantic_zoom_engine import SemanticZoomEngine
from backend.interactive.svg_interaction_builder import SVGInteractionBuilder
from backend.interactive.drilldown_engine import DrilldownEngine
from backend.interactive.metadata_exporter import RTLMetadataExporter

# ============================================================
# PHASE 7
# ============================================================

from backend.timing.timing_engine import TimingEngine
from backend.timing.path_visualizer import TimingPathVisualizer
from backend.timing.slack_estimator import SlackEstimator
from backend.timing.clock_domain_analyzer import ClockDomainAnalyzer

# ============================================================
# PHASE 8
# ============================================================
from backend.placement.placement_predictor import PlacementPredictor
# ============================================================
# PHASE 9
# ============================================================
from backend.cdc.clock_domain_crossing import CDCAnalyzer
# ============================================================
# PHASE 10
# ============================================================
from backend.orchestrator.aidea_orchestrator import AIDEAOrchestrator

# ================================================================
# GLOBAL CONFIGURATION
# ================================================================

ENGINE_CONFIG = {

    "DEFAULT_LAYOUT": "dot",

    "LARGE_GRAPH_LAYOUT": "sfdp",

    "FSM_LAYOUT": "circo",

    "PIPELINE_LAYOUT": "dot",

    "MAX_VISIBLE_NODES": 800,

    "MAX_VISIBLE_EDGES": 2500,

    "AUTO_CLUSTER_THRESHOLD": 4,

    "AUTO_BUS_THRESHOLD": 4,

    "HIERARCHY_THRESHOLD": 5,

    "ENABLE_DEBUG": False,

    "ENABLE_BUS_COMPRESSION": True,

    "ENABLE_CLUSTERING": True,

    "ENABLE_PIPELINE_DETECTION": True,

    "ENABLE_FSM_DETECTION": True,

    "ENABLE_MEMORY_ABSTRACTION": True,

    "ENABLE_REGISTER_BANKS": True,

    "ENABLE_CARRY_CHAIN": True,

    "ENABLE_GRAPH_SIMPLIFICATION": True,

    "ENABLE_DOT_CLEANUP": True,

    "ENABLE_HIERARCHY": True,

    "ENABLE_INTERACTIVE_HINTS": True,

    "SVG_MODE": True,

    "DPI": "180"
}

# ================================================================
# CONTROL SIGNALS
# ================================================================

CONTROL_SIGNALS = [

    "CLK",
    "CLOCK",
    "ACLK",

    "RST",
    "RESET",
    "RESETN",
    "RESET_N",

    "ENABLE",
    "EN",
    "CE",
    "WE",

    "VALID",
    "READY"
]

# ================================================================
# UTILITY FUNCTIONS
# ================================================================


def debug_print(*args):

    if ENGINE_CONFIG["ENABLE_DEBUG"]:

        print("[DEBUG]", *args)


# ================================================================
# SANITIZATION
# ================================================================


def sanitize_graphviz_id(name):

    if name is None:

        return "UNKNOWN"

    name = str(name)

    name = re.sub(

        r'[^a-zA-Z0-9_\[\]:]',
        '_',
        name
    )

    if len(name) == 0:

        name = "EMPTY"

    if name[0].isdigit():

        name = "N_" + name

    return name


# ================================================================
# VECTOR / BUS DETECTION
# ================================================================


def is_vector_signal(signal_name):

    signal_name = str(signal_name)

    return (

        "[" in signal_name
        and
        "]" in signal_name
    )


# ================================================================
# VECTOR WIDTH EXTRACTION
# ================================================================


def extract_bus_width(signal_name):

    signal_name = str(signal_name)

    match = re.search(

        r'\[(\d+)\:(\d+)\]',
        signal_name
    )

    if match:

        msb = int(match.group(1))
        lsb = int(match.group(2))

        return abs(msb - lsb) + 1

    return 1

# ================================================================
# GLOBAL RTL BUS DATABASE
# ================================================================

GLOBAL_BUS_MAP = {}


# ================================================================
# GENERIC BUS ENGINE
# ================================================================

# ================================================================
# GENERIC VECTOR DETECTOR
# ================================================================

def is_generic_bus(signal_name):

    signal_name = str(signal_name)

    base = re.sub(
        r'\[\d+(:\d+)?\]',
        '',
        signal_name
    )

    # ============================================================
    # DIRECT VECTOR
    # ============================================================

    if "[" in signal_name:

        return True

    # ============================================================
    # RTL PORT DATABASE
    # ============================================================

    if base.upper() in GLOBAL_BUS_MAP:

        return True

    return False

# ================================================================
# GENERIC BUS LABEL FORMAT
# ================================================================

def generic_bus_label(signal_name):

    signal_name = str(signal_name)

    match = re.search(
        r'(.*)\[(\d+)\:(\d+)\]',
        signal_name
    )

    if match:

        name = match.group(1).upper()

        msb = match.group(2)
        lsb = match.group(3)

        return f"{name}[{msb}:{lsb}]"

    single = re.search(
        r'(.*)\[(\d+)\]',
        signal_name
    )

    if single:

        return single.group(1).upper()

    return signal_name.upper()




# ================================================================
# INTERNAL TEMP NET FILTER
# ================================================================


def is_internal_temp_net(net_name):

    net_name = str(net_name)

    temp_patterns = [

        "$",
        "_tmp",
        "temp",
        "_abc_",
        "_TECHMAP_",
        "$auto",
        "$flatten"
    ]

    for pattern in temp_patterns:

        if pattern.lower() in net_name.lower():

            return True

    return False


# ================================================================
# CONTROL SIGNAL DETECTION
# ================================================================


def is_control_signal(name):

    name = str(name).upper()

    for sig in CONTROL_SIGNALS:

        if sig in name:

            return True

    return False


# ================================================================
# CELL LABELING
# ================================================================


def clean_cell_label(cell_type):

    cell_type = str(cell_type)

    clean_type = cell_type.replace(
        "$",
        ""
    ).lower()

    CELL_MAP = {

        "and": "AND",
        "or": "OR",
        "xor": "XOR",
        "xnor": "XNOR",
        "not": "NOT",
        "nand": "NAND",
        "nor": "NOR",
        "buf": "BUFFER",

        "add": "Adder",
        "sub": "Subtractor",
        "mul": "Multiplier",
        "div": "Divider",
        "mod": "Modulo",
        "alu": "ALU",

        "mux": "MUX",
        "demux": "DEMUX",
        "decoder": "Decoder",
        "encoder": "Encoder",

        "dff": "DFF",
        "tff": "TFF",
        "jkff": "JKFF",
        "srff": "SRFF",
        "latch": "Latch",
        "register": "Register",

        "ram": "RAM",
        "rom": "ROM",
        "fifo": "FIFO",
        "cache": "CACHE",
        "memory": "MEMORY",

        "driver": "Driver",
        "tristate": "Tri-State",
        "io": "IO Buffer",

        "pll": "PLL",
        "clock": "Clock",
        "reset": "Reset Logic"
    }

    for keyword, label in CELL_MAP.items():

        if keyword in clean_type:

            return label

    return clean_type.upper()


# ================================================================
# CELL COLOR ENGINE
# ================================================================


def get_cell_color(cell_type):

    cell_type = str(cell_type).lower()

    if any(x in cell_type for x in [

        "and",
        "or",
        "xor",
        "nand",
        "nor",
        "not",
        "buf"
    ]):

        return "lightyellow"

    elif any(x in cell_type for x in [

        "add",
        "sub",
        "mul",
        "div",
        "alu"
    ]):

        return "lightgreen"

    elif "mux" in cell_type:

        return "orange"

    elif any(x in cell_type for x in [

        "dff",
        "tff",
        "jkff",
        "srff",
        "latch",
        "register"
    ]):

        return "lightblue"

    elif any(x in cell_type for x in [

        "ram",
        "rom",
        "fifo",
        "cache",
        "memory"
    ]):

        return "plum"

    elif any(x in cell_type for x in [

        "driver",
        "tristate",
        "buffer"
    ]):

        return "lightcyan"

    return "lightgray"


# ================================================================
# EDGE STYLE ENGINE
# ================================================================


def get_edge_style(conn_name, signal_name=""):

    edge_color = "black"

    edge_style = "solid"

    penwidth = "1.0"

    conn_upper = str(conn_name).upper()

    if conn_upper in [

        "CLK",
        "CLOCK"
    ]:

        edge_color = "blue"
        edge_style = "bold"
        penwidth = "2.5"

    elif conn_upper in [

        "RST",
        "RESET",
        "RESETN"
    ]:

        edge_color = "red"
        edge_style = "dashed"
        penwidth = "2.2"

    elif conn_upper in [

        "ENABLE",
        "EN",
        "CE"
    ]:

        edge_color = "green"
        edge_style = "dotted"
        penwidth = "1.5"

    elif conn_upper in [

        "CARRY",
        "CIN",
        "COUT"
    ]:

        edge_color = "darkgreen"
        edge_style = "bold"
        penwidth = "2.8"

    if is_vector_signal(signal_name):

        penwidth = "4.0"
        edge_style = "bold"
        edge_color = "#006400"

    return edge_color, edge_style, penwidth


# ================================================================
# RTL ANALYZER
# ================================================================


class RTLAnalyzer:

    def __init__(self, cells):

        self.cells = cells

        self.analysis = {}

    def analyze(self):

        self.analysis["total_cells"] = len(self.cells)

        self.analysis["sequential_cells"] = 0

        self.analysis["combinational_cells"] = 0

        self.analysis["memory_cells"] = 0

        self.analysis["muxes"] = 0

        self.analysis["adders"] = 0

        self.analysis["hierarchical_modules"] = set()

        self.analysis["repeated_types"] = Counter()

        for cell in self.cells:

            ctype = str(cell.get("type", "")).lower()

            self.analysis["repeated_types"][ctype] += 1

            if any(x in ctype for x in [

                "dff",
                "ff",
                "latch",
                "register"
            ]):

                self.analysis["sequential_cells"] += 1

            else:

                self.analysis["combinational_cells"] += 1

            if any(x in ctype for x in [

                "ram",
                "rom",
                "fifo",
                "memory"
            ]):

                self.analysis["memory_cells"] += 1

            if "mux" in ctype:

                self.analysis["muxes"] += 1

            if "add" in ctype:

                self.analysis["adders"] += 1

        total = max(1, self.analysis["total_cells"])

        self.analysis["sequential_ratio"] = (
            self.analysis["sequential_cells"] / total
        )

        return self.analysis


# ================================================================
# STRUCTURE DETECTOR
# ================================================================


def detect_structures(cells):

    structures = {

        "adders": [],
        "dffs": [],
        "muxes": [],
        "logic": [],

        "fsm": [],
        "register_banks": [],
        "carry_chains": [],
        "pipelines": [],

        "memories": [],
        "drivers": [],

        "repeated_blocks": defaultdict(list)
    }

    for cell in cells:

        cell_name = str(
            cell.get(
                "name",
                ""
            )
        ).lower()

        cell_type = str(
            cell.get(
                "type",
                ""
            )
        ).lower()

        structures["repeated_blocks"][cell_type].append(cell)

        if "state" in cell_name:

            structures["fsm"].append(cell)

        elif "add" in cell_type:

            structures["adders"].append(cell)

        elif "dff" in cell_type or "ff" in cell_type:

            structures["dffs"].append(cell)

        elif "mux" in cell_type:

            structures["muxes"].append(cell)

        elif any(x in cell_type for x in [

            "ram",
            "rom",
            "fifo",
            "memory"
        ]):

            structures["memories"].append(cell)

        elif any(x in cell_type for x in [

            "driver",
            "buffer"
        ]):

            structures["drivers"].append(cell)

        else:

            structures["logic"].append(cell)

    if len(structures.get("dffs", [])) >= 16:

        structures["register_banks"].append({

            "name": "REGISTER_BANK",

            "cells": structures["dffs"]
        })

    if len(structures["adders"]) >= 2:

        structures["carry_chains"] = structures[
            "adders"
        ]

    if len(structures["dffs"]) >= 2:

        structures["pipelines"] = structures[
            "dffs"
        ]

    return structures


# ================================================================
# LAYOUT ENGINE
# ================================================================


class LayoutEngine:

    def __init__(self, analysis):

        self.analysis = analysis

    def choose_engine(self):

        total = self.analysis["total_cells"]

        seq_ratio = self.analysis["sequential_ratio"]

        if total > 400:

            return "sfdp"

        if seq_ratio > 0.4:

            return "dot"

        return "dot"

    def choose_rankdir(self):

        return "LR"


# ================================================================
# CLUSTER ENGINE
# ================================================================


class ClusterEngine:

    def __init__(self, dot):

        self.dot = dot

    def create_cluster(self, name, label, color):

        return self.dot.subgraph(name=name)
    
    
# ================================================================
# GENERIC BUS LABEL FORMATTER
# ================================================================
# ================================================================
# GENERIC BUS LABEL FORMATTER
# ================================================================

def format_bus_label(signal_name):

    signal_name = str(signal_name)

    # ============================================================
    # FULL VECTOR
    # ============================================================

    full_match = re.search(
        r'(.*)\[(\d+):(\d+)\]',
        signal_name
    )

    if full_match:

        base = full_match.group(1)

        msb = full_match.group(2)
        lsb = full_match.group(3)

        return f"{base.upper()}[{msb}:{lsb}]"

    # ============================================================
    # SINGLE BIT VECTOR
    # ============================================================

    single_match = re.search(
        r'(.*)\[(\d+)\]',
        signal_name
    )

    if single_match:

        base = single_match.group(1)

        # ========================================================
        # COLLAPSE TO GLOBAL BUS
        # ========================================================

        if base in GLOBAL_BUS_MAP:

            return GLOBAL_BUS_MAP[base]["full"].upper()

        # ========================================================
        # REMOVE FLOATING SINGLE BIT
        # ========================================================

        return None

    # ============================================================
    # NORMAL SIGNAL
    # ============================================================

    return signal_name.upper()


# ================================================================
# PORT CLUSTERS
# ================================================================
# ================================================================
# ================================================================
# INPUT CLUSTER
# ================================================================

def create_input_cluster(dot, rtl_inputs):

    with dot.subgraph(name="cluster_inputs") as inp:
        inp.attr(
            label="INPUTS",
            color="green",
            fontcolor="darkgreen",
            penwidth="2.2",
            style="rounded"
        )

        inp.attr(rank="source")

        for port in rtl_inputs:

            port_name = port["name"]
            
            # ========================================================
            # REMOVE SINGLE-BIT VECTOR PORTS
            # ========================================================

            if re.search(r'.*\[\d+\]$', str(port_name)):

                base_signal = re.sub(

                    r'\[\d+\]',

                    '',

                    port_name
                )

                if base_signal in GLOBAL_BUS_MAP:

                    continue
            

            display_name = format_bus_label(port_name)
            
            if display_name is None:
                continue

            safe_port = sanitize_graphviz_id(
                display_name
            )

            inp.node(
                safe_port,
                display_name,
                shape="oval",
                style="filled",
                fillcolor="#7CFC7C",
                color="darkgreen",
                penwidth="1.5",
                width="1.0"
            )



        # ========================================================
        # FORCE ANCHOR INSIDE CLUSTER
        # ========================================================

        if len(rtl_inputs) > 0:

            first_port = format_bus_label(
                rtl_inputs[0]["name"]
            )

            
            
            


# ================================================================
# CONTROL CLUSTER
# ================================================================


def create_control_cluster(dot, rtl_inputs):

    with dot.subgraph(name="cluster_control") as ctrl:

        ctrl.attr(

            label="CONTROL",

            color="gold",

            style="rounded"
        )

        ctrl.attr(rank="source")

        for port in rtl_inputs:

            port_name = port["name"]

            if not is_control_signal(port_name):

                continue

            safe_port = sanitize_graphviz_id(
                port_name
            )

            ctrl.node(

                safe_port,

                port_name,

                shape="oval",

                style="filled",

                fillcolor="gold",

                width="1.0"
            )
            
             

            


# ================================================================
# OUTPUT CLUSTER
# ================================================================
# ================================================================
# OUTPUT CLUSTER
# ================================================================

def create_output_cluster(dot, rtl_outputs):

    with dot.subgraph(name="cluster_outputs") as out:

        out.attr(
            label="OUTPUTS",
            color="red",
            fontcolor="darkred",
            penwidth="2.2",
            style="rounded"
        )

        out.attr(rank="sink")

        for port in rtl_outputs:

            port_name = port["name"]
            
            # ========================================================
            # REMOVE SINGLE-BIT VECTOR PORTS
            # ========================================================

            if re.search(r'.*\[\d+\]$', str(port_name)):

                base_signal = re.sub(

                    r'\[\d+\]',

                    '',

                    port_name
                )

                if base_signal in GLOBAL_BUS_MAP:

                    continue

            display_name = format_bus_label(port_name)
            if display_name is None:
                continue

            safe_port = sanitize_graphviz_id(
                display_name
            )

            out.node(
                safe_port,
                display_name,
                shape="oval",
                style="filled",
                fillcolor="#FFB6C1",
                color="darkred",
                penwidth="1.5",
                width="1.0"
            )



        # ========================================================
        # FORCE INSIDE CLUSTER
        # ========================================================

        if len(rtl_outputs) > 0:

            first_port = format_bus_label(
                rtl_outputs[0]["name"]
            )
            
            
            

# ================================================================
# LOGIC CLUSTER
# ================================================================

def create_logic_cluster(

    dot,

    structures,

    abstractions,

    top_module="module_name"
):

    with dot.subgraph(name="cluster_logic") as logic:
        logic.attr(rank="same")

        # ============================================================
        # CLUSTER STYLE
        # ============================================================

        logic.attr(

            label="RTL LOGIC",

            color="gray",

            style="rounded",

            penwidth="1.2"
        )
        
        
        # ============================================================
            # GENERIC SEMANTIC RTL BLOCK
        # ============================================================

        semantic_label = top_module

        if len(abstractions.get("arithmetic", [])) > 0:

                semantic_label += "\\n(Arithmetic RTL)"

        elif len(abstractions.get("fsm", [])) > 0:

                semantic_label += "\\n(FSM RTL)"

        elif len(abstractions.get("pipelines", [])) > 0:

                semantic_label += "\\n(Pipeline RTL)"

        elif len(abstractions.get("register_banks", [])) > 0:

                semantic_label += "\\n(Register RTL)"

        else:

                semantic_label += "\\n(Generic RTL)"

        logic.node(
                sanitize_graphviz_id(top_module),
                semantic_label,
                shape="box",
                style="filled,rounded",
                fillcolor="#90EE90",
                color="darkgreen",
                penwidth="3.0",
                width="4.0",
                height="1.4",
                fontsize="16"
            )
        
        


        # ============================================================
        # FSM ABSTRACTION
        # ============================================================

        if len(

            structures.get(
                "fsm",
                []
            )

        ) > 0:

            logic.node(

                "FSM_BLOCK",

                "FSM",

                shape="box",

                style="filled,rounded",

                fillcolor="plum",

                width="2.4",

                height="1.1",

                fontsize="12"
            )

        # ============================================================
        # REGISTER BANK ABSTRACTION
        # ============================================================

        if len(

            structures.get(
                "register_banks",
                []
            )

        ) > 0:

            logic.node(

                "REGISTER_BANK",

                shape="box",

                style="filled,rounded",

                fillcolor="#A8D8F0",

                width="2.6",

                height="1.1",

                fontsize="12"
            )
            


        # ============================================================
        # GENERIC REPEATED BLOCK CLUSTERING
        # ============================================================

        repeated_blocks = structures.get(
            "repeated_blocks",
            {}
        )

        for cell_type, group in repeated_blocks.items():

            # ========================================================
            # SKIP EMPTY GROUPS
            # ========================================================

            if len(group) == 0:

                continue

            # ========================================================
            # CLUSTER THRESHOLD
            # ========================================================

            if len(group) < ENGINE_CONFIG[
                "AUTO_CLUSTER_THRESHOLD"
            ]:

                continue
            
            # ============================================================
            # DO NOT CLUSTER SEQUENTIAL CELLS
            # ============================================================

            if any(

                x in str(cell_type).lower()

                for x in [

                    "dff",
                    "ff",
                    "register",
                    "latch"
                ]
            ):

                continue
            
            # ========================================================
            # SKIP ARITHMETIC CLUSTERING
            # ========================================================

            if any(

                x in str(cell_type).lower()

                for x in [

                    "add",
                    "fa",
                    "ha",
                    "carry"
                ]
            ):

                continue

            # ========================================================
            # GENERIC LABEL
            # ========================================================

            label = clean_cell_label(
                cell_type
            )

            node_name = sanitize_graphviz_id(

                f"GROUP_{cell_type}"
            )

            # ========================================================
            # GENERIC CLUSTER NAME
            # ========================================================

            cluster_label = (

                f"{label} CLUSTER x{len(group)}"
            )

            # ========================================================
            # GENERIC COLOR
            # ========================================================

            cluster_color = get_cell_color(
                cell_type
            )

            # ========================================================
            # CREATE CLUSTER NODE
            # ========================================================

            logic.node(

                node_name,

                cluster_label,

                shape="box",

                style="filled,rounded",

                fillcolor=cluster_color,

                width="1.8",

                height="1.2",

                fontsize="11"
            )

        # ============================================================
        # SEMANTIC MODE CHECK
        # ============================================================
        # Mirrors the has_semantic_abstraction / semantic_mode flag
        # computed later in generate_schematic() (which wipes `cells`
        # and skips signal-level wiring for FSM / arithmetic /
        # pipeline / register-bank designs). create_logic_cluster()
        # runs BEFORE that flag exists, so without this check it drew
        # every raw gate from structures["logic"] with no wires at
        # all whenever semantic abstraction was about to kick in.

        has_semantic_abstraction = (

            len(abstractions.get("arithmetic", [])) > 0 or
            len(abstractions.get("fsm", [])) > 0 or
            len(abstractions.get("pipelines", [])) > 0 or
            len(abstractions.get("register_banks", [])) > 0
        )

        # ============================================================
        # GENERIC LOGIC CELLS
        # ============================================================

        if not has_semantic_abstraction:

            for cell in structures.get("logic", []):
            
              # ====================================================
              # SKIP CELLS ALREADY ABSTRACTED
              # ====================================================

              if cell.get("abstracted", False):

                  continue

              cell_name = cell.get(
                  "name",
                  "UNKNOWN"
              )

              cell_type = cell.get(
                  "type",
                  "UNKNOWN"
              )

              safe_cell_name = sanitize_graphviz_id(
                  cell_name
              )

              label = clean_cell_label(
                  cell_type
              )

              color = get_cell_color(
                  cell_type
              )

              # ========================================================
              # SKIP IF CELL BELONGS TO GROUPED CLUSTER
              # ========================================================

              grouped = False

              for repeated_type, group in repeated_blocks.items():

                  if (

      len(group) >= ENGINE_CONFIG[
          "AUTO_CLUSTER_THRESHOLD"
      ]

      and

      not any(

          x in repeated_type.lower()

          for x in [

              "dff",
              "ff",
              "register",
              "latch"
          ]
      )
  ):

                      if cell in group:

                          grouped = True

              if grouped:

                  continue

              # ========================================================
              # GENERIC CELL STYLE
              # ========================================================

              node_shape = "box"

              node_width = "1.5"

              node_height = "0.8"

              # ========================================================
              # MEMORY STYLE
              # ========================================================

              if any(

                  x in str(cell_type).lower()

                  for x in [

                      "ram",
                      "rom",
                      "fifo",
                      "memory"
                  ]
              ):

                  node_shape = "cylinder"

                  node_width = "2.0"

                  node_height = "1.0"

              # ========================================================
              # MUX STYLE
              # ========================================================

              elif "mux" in str(cell_type).lower():

                  node_shape = "trapezium"

              # ========================================================
              # SEQUENTIAL STYLE
              # ========================================================

              elif any(

                  x in str(cell_type).lower()

                  for x in [

                      "dff",
                      "ff",
                      "latch",
                      "register"
                  ]
              ):

                  node_shape = "box"
                  node_width = "1.2"
                  node_height = "0.6"

              # ========================================================
              # CREATE GENERIC NODE
              # ========================================================

              logic.node(

                  safe_cell_name,

                  label,

                  shape=node_shape,

                  style="filled,rounded",

                  fillcolor=color,

                  width=node_width,

                  height=node_height,

                  fontsize="10"
              )
            

# ================================================================
# GRAPH METRICS
# ================================================================


class GraphMetrics:

    def __init__(self):

        self.node_count = 0

        self.edge_count = 0

        self.bus_count = 0

        self.control_count = 0

    def report(self):

        return {

            "nodes": self.node_count,
            "edges": self.edge_count,
            "buses": self.bus_count,
            "controls": self.control_count
        }


# ================================================================
# SIGNAL FILTER ENGINE
# ================================================================


def should_draw_internal_signal(signal_name):

    signal_name = str(signal_name)

    if is_internal_temp_net(signal_name):

        return False

    if signal_name.startswith("$"):

        return False

    if signal_name.startswith("_"):

        return False

    if "unused" in signal_name.lower():

        return False

    return True


# ================================================================
# SIGNAL IMPORTANCE ENGINE
# ================================================================


def is_meaningful_signal(signal_name):

    signal_name = str(signal_name)

    if signal_name in ["0", "1"]:

        return False

    if signal_name.startswith("$"):

        return False

    if "unused" in signal_name.lower():

        return False

    return True


# ================================================================
# CONNECTION DIRECTION ENGINE
# ================================================================


class ConnectionDirectionEngine:

    def __init__(self, rtl_inputs, rtl_outputs):

        self.input_ports = set()

        self.output_ports = set()

        for port in rtl_inputs:

            self.input_ports.add(

                re.sub(
                    r'\[\d+(:\d+)?\]',
                    '',
                    port["name"]
                )
            )

        for port in rtl_outputs:

            self.output_ports.add(

                re.sub(
                    r'\[\d+(:\d+)?\]',
                    '',
                    port["name"]
                )
            )

    def get_direction(self, signal_name):

        base = re.sub(
            r'\[\d+(:\d+)?\]',
            '',
            signal_name
        )

        if base in self.input_ports:

            return "INPUT"

        if base in self.output_ports:

            return "OUTPUT"

        return "INTERNAL"


# ================================================================
# GRAPH CLEANER
# ================================================================


class GraphCleaner:

    def __init__(self):

        self.seen_edges = set()

    def should_keep_edge(self, src, dst):

        edge_key = f"{src}->{dst}"

        if edge_key in self.seen_edges:

            return False

        self.seen_edges.add(edge_key)

        return True


# ================================================================
# GRAPH DENSITY ENGINE
# ================================================================


class GraphDensityEngine:

    def __init__(self, cells):

        self.cells = cells

    def get_density(self):

        total_connections = 0

        for cell in self.cells:

            connections = cell.get("connections", {})

            total_connections += len(connections)

        return total_connections


# ================================================================
# PIPELINE VISUALIZER
# ================================================================


class PipelineVisualizer:

    def __init__(self, dot):

        self.dot = dot

    def align_pipeline(self, pipeline_cells):

        for i in range(len(pipeline_cells) - 1):

            curr_stage = sanitize_graphviz_id(
                pipeline_cells[i]["name"]
            )

            next_stage = sanitize_graphviz_id(
                pipeline_cells[i + 1]["name"]
            )

            self.dot.edge(

                curr_stage,

                next_stage,

                style="invis",

                weight="50"
            )


# ================================================================
# FSM VISUALIZER
# ================================================================


class FSMVisualizer:

    def __init__(self, dot):

        self.dot = dot

    def create_fsm_node(self):

        self.dot.node(

            "FSM_BLOCK",

            "FSM",

            shape="box",

            style="filled,rounded",

            fillcolor="plum",

            width="2.2",

            height="1.0"
        )


# ================================================================
# MEMORY VISUALIZER
# ================================================================


class MemoryVisualizer:

    def __init__(self, dot):

        self.dot = dot

    def create_memory(self, name, label):

        self.dot.node(

            sanitize_graphviz_id(name),

            label,

            shape="cylinder",

            style="filled",

            fillcolor="plum"
        )


# ================================================================
# RTL FLOW ROUTER
# ================================================================

# ================================================================
# SYNTHESIS STATISTICS ENGINE
# ================================================================

def generate_synthesis_statistics(

    cells,

    rtl_inputs,

    rtl_outputs,

    internal_signals
):

    stats = Counter()

    # ============================================================
    # CELL ANALYSIS
    # ============================================================

    for cell in cells:

        ctype = str(
            cell.get(
                "type",
                ""
            )
        ).lower()

        # ========================================================
        # LOGIC GATES
        # ========================================================

        if "and" in ctype:

            stats["AND"] += 1

        elif "nand" in ctype:

            stats["NAND"] += 1

        elif "or" in ctype:

            stats["OR"] += 1

        elif "ornot" in ctype:

            stats["ORNOT"] += 1

        elif "xor" in ctype:

            stats["XOR"] += 1

        elif "xnor" in ctype:

            stats["XNOR"] += 1

        elif "not" in ctype:

            stats["NOT"] += 1

        elif "nor" in ctype:

            stats["NOR"] += 1

        # ========================================================
        # RTL BLOCKS
        # ========================================================

        elif "mux" in ctype:

            stats["MUX"] += 1

        elif "dff" in ctype:

            stats["DFF"] += 1

        elif "ff" in ctype:

            stats["FLIPFLOP"] += 1

        elif "latch" in ctype:

            stats["LATCH"] += 1

        elif "register" in ctype:

            stats["REGISTER"] += 1

        # ========================================================
        # ARITHMETIC
        # ========================================================

        elif "add" in ctype:

            stats["ADDERS"] += 1

        elif "sub" in ctype:

            stats["SUBTRACTORS"] += 1

        elif "mul" in ctype:

            stats["MULTIPLIERS"] += 1

        elif "div" in ctype:

            stats["DIVIDERS"] += 1

        elif "alu" in ctype:

            stats["ALU"] += 1

        # ========================================================
        # MEMORY
        # ========================================================

        elif "ram" in ctype:

            stats["RAM"] += 1

        elif "rom" in ctype:

            stats["ROM"] += 1

        elif "fifo" in ctype:

            stats["FIFO"] += 1

        elif "memory" in ctype:

            stats["MEMORY"] += 1

    # ============================================================
    # SIGNAL COUNTS
    # ============================================================

    stats["INPUT SIGNALS"] = len(
        rtl_inputs
    )

    stats["OUTPUT SIGNALS"] = len(
        rtl_outputs
    )

    stats["INTERNAL SIGNALS"] = len(
        internal_signals
    )

    # ============================================================
    # TOTAL CELLS
    # ============================================================

    stats["TOTAL CELLS"] = len(
        cells
    )

    return stats

# ================================================================
# MAIN SCHEMATIC GENERATOR
# ================================================================

def generate_schematic(

    cells,

    net_map,

    rtl_inputs,

    rtl_outputs,
    
    top_module="module_name",

    output_prefix="rtl_schematic"
):

    # ============================================================
    # RTL ANALYSIS
    # ============================================================

    analyzer = RTLAnalyzer(cells)

    analysis = analyzer.analyze()

    structures = detect_structures(cells)

    metrics = GraphMetrics()
    
    abstraction_engine = RTLAbstractionEngine(cells)

    abstractions = abstraction_engine.analyze()

    cells = abstraction_engine.mark_abstracted_cells()
    
    datapath_engine = DatapathEngine(

        cells,

        abstractions
    )
    datapath_layers = datapath_engine.build()
    
    ai_engine = AIRTLAnalyzer(

        cells,

        net_map,

        abstractions
    )

    ai_analysis = ai_engine.analyze()
    
    hierarchy_engine = HierarchyExplorer()

    zoom_engine = SemanticZoomEngine()

    interaction_builder = SVGInteractionBuilder()

    drilldown_engine = DrilldownEngine()

    metadata_exporter = RTLMetadataExporter()
    
    # ============================================================
    # PHASE 7
    # ============================================================

    # ------------------------------------------------------------
    # CREATE SIMPLE CRITICAL PATH ESTIMATION
    # ------------------------------------------------------------

    critical_paths = []

    for cell in cells:

        delay = round(

            len(
                cell.get(
                    "connections",
                    {}
                )
            ) * 0.35,

            2
        )

        slack = round(

            5.0 - delay,

            2
        )

        critical_paths.append({

            "startpoint": "START",

            "endpoint": cell.get(
                "name",
                "UNKNOWN"
            ),

            "delay": delay,

            "arrival_time": delay,

            "slack": slack,

            "status": (
                "SAFE"
                if slack >= 0
                else "VIOLATION"
            ),

            "violation_type": "setup"
        })

    # ------------------------------------------------------------
    # TIMING ENGINE
    # ------------------------------------------------------------

    timing_engine = TimingEngine(
        critical_paths
    )

    path_visualizer = TimingPathVisualizer()

    slack_estimator = SlackEstimator()

    # ------------------------------------------------------------
    # CLOCK DOMAIN ANALYSIS
    # ------------------------------------------------------------

    clock_analyzer = ClockDomainAnalyzer(
        cells
    )

    clock_domains = clock_analyzer.analyze()
    

    
    # ============================================================
    # PHASE 8 — PLACEMENT PREDICTION
    # ============================================================

    placement_engine = PlacementPredictor(
        cells
    )

    placement_map = placement_engine.predict()
    
    # ============================================================
    # PHASE 9 — CDC ANALYSIS
    # ============================================================

    cdc_engine = CDCAnalyzer(
        cells
    )

    cdc_domains = cdc_engine.analyze()
    
    # ============================================================
    # PHASE 10 — AIDEA ORCHESTRATOR
    # ============================================================

    orchestrator = AIDEAOrchestrator()

    orchestrator.register(

        "abstraction",

        abstraction_engine
    )

    orchestrator.register(

        "datapath",

        datapath_engine
    )

    orchestrator.register(

        "ai",

        ai_engine
    )

    orchestrator.register(

        "timing",

        timing_engine
    )
                
    
    # ============================================================
    # BUILD GLOBAL BUS DATABASE
    # ============================================================

    GLOBAL_BUS_MAP.clear()

    for port in rtl_inputs + rtl_outputs:

        pname = str(port["name"])

        match = re.search(
            r'(.*)\[(\d+):(\d+)\]',
            pname
        )

        if match:

            base = match.group(1)

            msb = int(match.group(2))
            lsb = int(match.group(3))

            GLOBAL_BUS_MAP[base] = {

                "width": abs(msb - lsb) + 1,

                "full": pname
            }

    # ============================================================
    # REMOVE EXPANDED SINGLE-BIT VECTOR PORTS
    # ============================================================

    clean_inputs = []

    for port in rtl_inputs:

        pname = str(port["name"])

        if re.search(r'.*\[\d+\]$', pname):

            base = re.sub(
                r'\[\d+\]',
                '',
                pname
            )

            if base in GLOBAL_BUS_MAP:

                continue

        clean_inputs.append(port)

    rtl_inputs = clean_inputs

    # ============================================================
    # CLEAN OUTPUTS
    # ============================================================

    clean_outputs = []

    for port in rtl_outputs:

        pname = str(port["name"])

        if re.search(r'.*\[\d+\]$', pname):

            base = re.sub(
                r'\[\d+\]',
                '',
                pname
            )

            if base in GLOBAL_BUS_MAP:

                continue

        clean_outputs.append(port)

    rtl_outputs = clean_outputs

    # ============================================================
    # LAYOUT ENGINE
    # ============================================================

    layout_engine = LayoutEngine(analysis)

    graph_engine = layout_engine.choose_engine()

    rankdir = layout_engine.choose_rankdir()

    # ============================================================
    # GRAPH INITIALIZATION
    # ============================================================

    dot = Digraph(

        comment="Generic RTL Schematic",

        engine=graph_engine
    )

    # ============================================================
    # GLOBAL GRAPH SETTINGS
    # ============================================================

   
    dot.attr(

        rankdir="LR",

        splines="polyline",

        overlap="false",

        nodesep="1.0",

        ranksep="1.8",

        bgcolor="white",

        compound="true",

        newrank="true",

        concentrate="false",

        dpi=str(ENGINE_CONFIG["DPI"])
    )
    dot.attr(

        "node",

        fontname="Helvetica"
    )

    
    

    # ============================================================
    # NODE STYLE
    # ============================================================

    dot.attr(

        "node",

        fontname="Arial",

        fontsize="11"
    )

    # ============================================================
    # EDGE STYLE
    # ============================================================

    dot.attr(

        "edge",

        fontname="Arial",

        fontsize="9"
    )

    # ============================================================
    # FLOW + CLEANUP ENGINES
    # ============================================================

    direction_engine = ConnectionDirectionEngine(

        rtl_inputs,

        rtl_outputs
    )

    flow_router = RTLFlowRouter(dot)
    
    # ============================================================
    # BUS ROUTER
    # ============================================================

    bus_router = GenericBusRouter(dot)

    graph_cleaner = GraphCleaner()

    # ============================================================
    # CREATE CLUSTERS
    # ============================================================

    create_input_cluster(
        dot,
        rtl_inputs
    )

    create_control_cluster(
        dot,
        rtl_inputs
    )

    create_logic_cluster(
        dot,
        structures,
        abstractions,
        top_module
    )

    create_output_cluster(
        dot,
        rtl_outputs
    )

    # ============================================================
    # EXISTING PORTS
    # ============================================================

    existing_ports = set()

    for port in rtl_inputs + rtl_outputs:

        pname = str(port["name"])

        # ========================================================
        # REMOVE SINGLE BIT VECTOR PORTS
        # ========================================================

        if re.search(r'\[\d+\]$', pname):

            base = re.sub(

                r'\[\d+\]',

                '',

                pname
            )

            if base in GLOBAL_BUS_MAP:

                continue

        # ========================================================
        # STORE FULL PORT NAME
        # ========================================================

        existing_ports.add(pname)

        # ========================================================
        # STORE BASE NAME
        # ========================================================

        existing_ports.add(

            re.sub(
                r'\[\d+(:\d+)?\]',
                '',
                pname
            )
        )

    # ============================================================
    # INTERNAL SIGNAL TRACKER
    # ============================================================

    internal_signals = {}
    
    
    # ============================================================
    # DETECT SEMANTIC ABSTRACTION
    # ============================================================

    has_semantic_abstraction = (

        len(abstractions.get("arithmetic", [])) > 0 or
        len(abstractions.get("fsm", [])) > 0 or
        len(abstractions.get("pipelines", [])) > 0 or
        len(abstractions.get("register_banks", [])) > 0
    )
        
        

    
    
    # ============================================================
    # DISABLE PRIMITIVE RENDERING IN SEMANTIC MODE
    # ============================================================

    if has_semantic_abstraction:

        cells = []

    # ============================================================
    # MAIN CONNECTION GENERATION
    # ============================================================

    # ============================================================
    # GLOBAL SEMANTIC MODE
    # ============================================================

    semantic_mode = any(

        len(v) > 0

        for v in abstractions.values()
    )
    
    # ============================================================
    # SKIP SIGNAL-LEVEL ROUTING IN SEMANTIC MODE
    # ============================================================

    if semantic_mode:

        cells = []

    # ============================================================
    # SIGNAL-LEVEL ROUTING
    # ============================================================

    for cell in cells:

        # ============================================================
        # FULL RTL SEMANTIC MODE
        # ============================================================

        if semantic_mode:

            continue
        
        # ============================================================
        # SKIP ABSTRACTED CELLS
        # ============================================================

        if cell.get("abstracted", False):

            continue

        cell_name = cell.get(
            "name",
            "UNKNOWN"
        )

        cell_type = str(
            cell.get(
                "type",
                "UNKNOWN"
            )
        ).lower()

        safe_cell_name = sanitize_graphviz_id(
            cell_name
        )
        
        # ============================================================
        # ROUTE TO ABSTRACT BLOCK
        # ============================================================

        for cluster in abstractions.get(

            "arithmetic",

            []
        ):

            if cell in cluster["cells"]:

                safe_cell_name = cluster["name"]

        # ========================================================
        # GENERIC REPEATED BLOCK CLUSTERING
        # ========================================================

        grouped = False

        repeated_blocks = structures.get(
            "repeated_blocks",
            {}
        )

        for repeated_type, group in repeated_blocks.items():

            # ========================================================
            # DO NOT COLLAPSE ARITHMETIC STRUCTURES
            # ========================================================

            arithmetic_keywords = [

                "add",
                "sub",
                "alu",
                "mul",
                "carry",
                "fa",
                "ha"
            ]

            if any(

                keyword in repeated_type.lower()

                for keyword in arithmetic_keywords
            ):

                continue

            # ========================================================
            # SAFE GROUPING
            # ========================================================

            if len(group) >= ENGINE_CONFIG[
                "AUTO_CLUSTER_THRESHOLD"
            ]:

                if cell in group:

                    safe_cell_name = sanitize_graphviz_id(

                        f"GROUP_{repeated_type}"
                    )

                    grouped = True

        # ========================================================
        # FSM ABSTRACTION
        # ========================================================

        if cell in structures.get("fsm", []):

            safe_cell_name = "FSM_BLOCK"

        # ========================================================
        # REGISTER BANK ABSTRACTION
        # ========================================================

        if cell in structures.get("dffs", []):

            if len(

                structures.get(
                    "register_banks",
                    []
                )

            ) > 0:

                safe_cell_name = "REGISTER_BANK"

        # ========================================================
        # CONNECTION EXTRACTION
        # ========================================================

        connections = cell.get(
            "connections",
            {}
        )
        
        drawn_buses = set()

        for conn_name, conn_value in connections.items():

            if not isinstance(conn_value, list):

                conn_value = [conn_value]

            # ====================================================
            # LOCAL BUS TRACKER
            # ====================================================

            

            for signal in conn_value:

                raw_signal = str(signal)

                signal_name = net_map.get(

                    str(raw_signal),

                    str(raw_signal)
                )
                
                # ============================================================
                # FULL SEMANTIC RTL MODE
                # ============================================================

                if semantic_mode:

                    continue
                
                # ============================================================
                # GENERIC BUS NORMALIZATION
                # ============================================================

                single_bit_match = re.search(

                    r'(.*)\[(\d+)\]',

                    signal_name
                )

                if single_bit_match:

                    base_signal = single_bit_match.group(1)
                    
                    
                    # ============================================================
                    # REMOVE SINGLE-BIT VECTOR LEAKAGE
                    # ============================================================

                    if base_signal in GLOBAL_BUS_MAP:

                        continue

                    # ========================================================
                    # MAP TO FULL RTL BUS
                    # ========================================================

                    if base_signal in GLOBAL_BUS_MAP:

                        signal_name = GLOBAL_BUS_MAP[
                            base_signal
                        ]["full"]
                
                # ============================================================
                # GENERIC ABSTRACTED SIGNAL FILTER
                # ============================================================

                skip_signal = False

                # ============================================================
                # CHECK ALL ABSTRACTION TYPES
                # ============================================================

                for abstraction_type, abstraction_list in abstractions.items():

                    for abstraction in abstraction_list:

                        abstraction_cells = abstraction.get(

                            "cells",

                            []
                        )

                        # ========================================================
                        # CURRENT CELL BELONGS TO ABSTRACTION
                        # ========================================================

                        if cell not in abstraction_cells:

                            continue

                        # ========================================================
                        # EXTRACT INTERNAL SIGNALS
                        # ========================================================

                        for abstract_cell in abstraction_cells:

                            connections = abstract_cell.get(

                                "connections",

                                {}
                            )

                            for conn_port, conn_signals in connections.items():

                                if not isinstance(conn_signals, list):

                                    conn_signals = [conn_signals]

                                for internal_signal in conn_signals:

                                    internal_signal = str(internal_signal)

                                    resolved_signal = net_map.get(

                                        internal_signal,

                                        internal_signal
                                    )

                                    # ====================================================
                                    # INTERNAL ABSTRACTED SIGNAL
                                    # ====================================================

                                    # ====================================================
                                    # INTERNAL ABSTRACTED SIGNAL ONLY
                                    # ====================================================

                                    base_signal = re.sub(

                                        r'\[\d+(:\d+)?\]',

                                        '',

                                        resolved_signal
                                    )

                                    # ====================================================
                                    # DO NOT REMOVE TOP RTL PORTS
                                    # ====================================================

                                    if (

                                        resolved_signal == signal_name

                                        and

                                        base_signal not in existing_ports
                                    ):

                                        skip_signal = True

                # ============================================================
                # SKIP INTERNAL ABSTRACTED ROUTING
                # ============================================================

                if skip_signal:

                    continue
                
                

                # =================================================
                # INVALID SIGNAL FILTER
                # =================================================

                if not is_meaningful_signal(signal_name):

                    continue

                # =================================================
                # TEMP NET FILTER
                # =================================================

                if ENGINE_CONFIG["ENABLE_DOT_CLEANUP"]:

                    if is_internal_temp_net(signal_name):

                        continue

                # =================================================
                # BUS COMPRESSION
                # =================================================

                bus_base = re.sub(

                    r'\[\d+(:\d+)?\]',

                    '',

                    signal_name
                )

                if ENGINE_CONFIG["ENABLE_BUS_COMPRESSION"]:

                    if is_generic_bus(signal_name):

                        if bus_base in drawn_buses:

                            continue

                        drawn_buses.add(bus_base)
                        
                        # ============================================================
                        # SKIP SINGLE-BIT VECTOR LEAKAGE
                        # ============================================================

                        if re.search(

                            r'.*\[\d+\]$',

                            raw_signal
                        ):

                            base_signal = re.sub(

                                r'\[\d+\]',

                                '',

                                raw_signal
                            )

                            if base_signal in GLOBAL_BUS_MAP:

                                continue

                # =================================================
                # SAFE SIGNAL
                # =================================================

                safe_signal = sanitize_graphviz_id(
                    signal_name
                )

                # =================================================
                # INTERNAL SIGNAL NODES
                # =================================================

                if (

                    signal_name not in existing_ports

                    and

                    safe_signal not in internal_signals
                ):

                    internal_signals[
                        safe_signal
                    ] = True

                    metrics.node_count += 1

                    if is_generic_bus(signal_name):

                        metrics.bus_count += 1

                    if should_draw_internal_signal(

                        signal_name
                    ):

                        # Internal routing node removed
                        # Prevent unnecessary floating wiring points
                        pass

                # =================================================
                # EDGE STYLE
                # =================================================

                edge_color, edge_style, penwidth = get_edge_style(

                        conn_name,

                        signal_name
                    )

                metrics.edge_count += 1

                # =================================================
                # SIGNAL DIRECTION
                # =================================================

                direction = direction_engine.get_direction(

                    signal_name
                )

                # =================================================
                # BUS SIGNALS
                # =================================================

                if is_generic_bus(signal_name):

                    direction = direction_engine.get_direction(
                        signal_name
                    )

                    if direction == "INPUT":

                        bus_router.register_driver(
                            signal_name,
                            sanitize_graphviz_id(signal_name)
                        )

                        bus_router.register_consumer(
                            signal_name,
                            safe_cell_name
                        )

                    elif direction == "OUTPUT":

                        bus_router.register_driver(
                            signal_name,
                            safe_cell_name
                        )

                        bus_router.register_consumer(
                            signal_name,
                            sanitize_graphviz_id(signal_name)
                        )

                    else:

                        # =================================================
                        # OUTPUT-LIKE PORT DETECTION
                        # =================================================

                        output_like_ports = [

                            "Y",
                            "Q",
                            "QN",
                            "OUT",
                            "SUM",
                            "S",
                            "CO",
                            "COUT",
                            "Z",
                            "RESULT",
                            "DATA_OUT",
                            "DOUT"
                        ]

                        is_output_port = any(

                            keyword in conn_name.upper()

                            for keyword in output_like_ports
                        )

                        if is_output_port:

                            bus_router.register_driver(

                                signal_name,

                                safe_cell_name
                            )

                        else:

                            bus_router.register_consumer(

                                signal_name,

                                safe_cell_name
                            )   

                    bus_router.create_bus_node(signal_name)

                    continue

                # =================================================
                # INPUT → LOGIC
                # =================================================

                if direction == "INPUT":

                    src = sanitize_graphviz_id(
                        signal_name
                    )

                    dst = safe_cell_name

                # =================================================
                # LOGIC → OUTPUT
                # =================================================

                elif direction == "OUTPUT":

                    src = safe_cell_name

                    dst = sanitize_graphviz_id(
                        signal_name
                    )

                # =================================================
                # INTERNAL SIGNALS
                # =================================================

                else:

                    continue

                # =================================================
                # INVALID EDGE FILTER
                # =================================================

                if src == dst:

                    continue

                if src == "":

                    continue

                if dst == "":

                    continue

                if safe_signal == safe_cell_name:

                    continue

                # =================================================
                # DUPLICATE EDGE FILTER
                # =================================================

                if not graph_cleaner.should_keep_edge(

                    src,

                    dst
                ):

                    continue

                # =================================================
                # GENERIC GROUP FILTER
                # =================================================

                if grouped:

                    allowed_ports = [

                        "A",
                        "B",
                        "Y",
                        "Q",
                        "D",
                        "CLK",
                        "RST",
                        "RESET",
                        "EN",
                        "ENABLE",
                        "CE",
                        "SUM",
                        "CIN",
                        "COUT",
                        "DATA",
                        "ADDR",
                        "OUT",
                        "IN"
                    ]

                    if conn_name.upper() not in allowed_ports:

                        continue

                # =================================================
                # EDGE ROUTING
                # =================================================

                if direction == "INPUT":

                    flow_router.route_input(

                        src,

                        dst,

                        edge_color,

                        edge_style,

                        penwidth
                    )

                elif direction == "OUTPUT":

                    flow_router.route_output(

                        src,

                        dst,

                        edge_color,

                        edge_style,

                        penwidth
                    )

                else:

                    flow_router.route_internal(

                        src,

                        dst,

                        edge_color,

                        edge_style,

                        penwidth
                    )

    # ============================================================
    # PIPELINE ALIGNMENT
    # ============================================================

    pipeline_cells = structures.get(
        "pipelines",
        []
    )

    for i in range(

        len(pipeline_cells) - 1
    ):

        curr_stage = sanitize_graphviz_id(

            pipeline_cells[i]["name"]
        )

        next_stage = sanitize_graphviz_id(

            pipeline_cells[i + 1]["name"]
        )

#        dot.edge(
#
#           curr_stage,
#
#           next_stage,
#
#           style="invis",
#
#           weight="25"
#       )

    # ============================================================
    # SYNTHESIS STATISTICS
    # ============================================================

    stats = generate_synthesis_statistics(

        cells,

        rtl_inputs,

        rtl_outputs,

        internal_signals
    )
    
    # ============================================================
    # INTERFACE-LEVEL RTL FLOW
    # ============================================================

    has_semantic_abstraction = any(

        len(v) > 0

        for v in abstractions.values()
    )

    # ============================================================
    # SEMANTIC DATAPATH VIEW
    # ============================================================

    if has_semantic_abstraction:

        # ========================================================
        # INPUTS → RTL BLOCK
        # ========================================================

        for port in rtl_inputs:

            port_name = port["name"]

            # ====================================================
            # REMOVE SINGLE BIT VECTOR LEAKAGE
            # ====================================================

            if re.search(r'.*\[\d+\]$', str(port_name)):

                base_signal = re.sub(

                    r'\[\d+\]',

                    '',

                    port_name
                )

                if base_signal in GLOBAL_BUS_MAP:

                    continue

            pname = format_bus_label(
                port_name
            )

            # ====================================================
            # INVALID/FLOATING SIGNAL FILTER
            # ====================================================

            if pname is None:

                continue

            if re.search(r'\[\d+\]$', str(pname)):

                continue

            src_node = sanitize_graphviz_id(pname)

            if src_node not in dot.body.__str__():

                continue

            dot.edge(

                src_node,

                sanitize_graphviz_id(top_module),

                color="blue",

                penwidth="3",

                minlen="2"
            )

        # ========================================================
        # RTL BLOCK → OUTPUTS
        # ========================================================

        for port in rtl_outputs:

            port_name = port["name"]

            # ====================================================
            # REMOVE SINGLE BIT VECTOR LEAKAGE
            # ====================================================

            if re.search(r'.*\[\d+\]$', str(port_name)):

                base_signal = re.sub(

                    r'\[\d+\]',

                    '',

                    port_name
                )

                if base_signal in GLOBAL_BUS_MAP:

                    continue

            pname = format_bus_label(
                port_name
            )

            # ====================================================
            # INVALID/FLOATING SIGNAL FILTER
            # ====================================================

            if pname is None:

                continue

            if re.search(r'\[\d+\]$', str(pname)):

                continue

            dst_node = sanitize_graphviz_id(pname)
            # ====================================================
            # VALID OUTPUT NODE ONLY
            # ====================================================

            if dst_node not in dot.body.__str__():

                continue

            # ====================================================
            # RTL BLOCK → OUTPUT PORT
            # ====================================================

            dot.edge(

                sanitize_graphviz_id(top_module),

                dst_node,

                color="darkgreen",

                penwidth="3",

                minlen="2"
            )

        
    # ============================================================
    # BUILD FINAL BUS TOPOLOGY
    # ============================================================

    bus_router.build_topology()


    # ============================================================
    # GRAPH RENDER
    # ============================================================

    try:

        dot.render(

            output_prefix,

            format="svg",

            cleanup=True
        )

        print("[INFO] SVG schematic generated")

    except Exception as e:

        print(

            "[ERROR] Graphviz render failed:",

            e
        )

    # ============================================================
    # METRICS
    # ============================================================

    print()

    print("=" * 60)

    print("GRAPH METRICS")

    print("=" * 60)

    print(metrics.report())

    print("=" * 60)

    # ============================================================
    # RETURN DATA
    # ============================================================

    return {

        "dot": dot,

        "stats": stats
    }