"""
============================================================

AIDEA Physical Design

Universal Design Object

This object is the central database used by

✔ Truth Table
✔ FSM
✔ Schematic
✔ Floorplanning
✔ Placement
✔ Routing
✔ Timing
✔ Power
✔ Congestion
✔ AI

============================================================
"""

from dataclasses import dataclass, field
from typing import Dict, List


# ==========================================================
# PORT
# ==========================================================

@dataclass
class Port:

    name: str

    direction: str

    bits: List[int] = field(default_factory=list)


# ==========================================================
# NET
# ==========================================================

@dataclass
class Net:

    name: str

    bits: List[int] = field(default_factory=list)


# ==========================================================
# CELL
# ==========================================================

@dataclass
class Cell:

    name: str

    cell_type: str

    connections: Dict = field(default_factory=dict)


# ==========================================================
# MODULE
# ==========================================================

@dataclass
class Module:

    name: str

    ports: List[Port] = field(default_factory=list)

    cells: List[Cell] = field(default_factory=list)

    nets: List[Net] = field(default_factory=list)


# ==========================================================
# DESIGN
# ==========================================================

@dataclass
class Design:

    top: str = ""

    modules: List[Module] = field(default_factory=list)

    metadata: Dict = field(default_factory=dict)