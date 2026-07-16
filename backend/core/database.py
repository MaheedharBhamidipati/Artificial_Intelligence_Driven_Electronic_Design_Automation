"""
============================================================

AIDEA Core Database

Universal Chip Database

Every backend module reads/writes this object.

============================================================
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


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

    attributes: Dict = field(default_factory=dict)


# ==========================================================
# MODULE
# ==========================================================

@dataclass
class Module:

    name: str

    ports: List[Port] = field(default_factory=list)

    nets: List[Net] = field(default_factory=list)

    cells: List[Cell] = field(default_factory=list)


# ==========================================================
# FLOORPLAN
# ==========================================================

@dataclass
class Floorplan:

    width: float = 0.0

    height: float = 0.0

    utilization: float = 0.0

    dead_space: float = 0.0

    macros: List = field(default_factory=list)


# ==========================================================
# PLACEMENT
# ==========================================================

@dataclass
class Placement:

    cells: List = field(default_factory=list)

    density: float = 0.0


# ==========================================================
# ROUTING
# ==========================================================

@dataclass
class Routing:

    wires: List = field(default_factory=list)

    congestion: float = 0.0


# ==========================================================
# TIMING
# ==========================================================

@dataclass
class Timing:

    critical_path: List = field(default_factory=list)

    slack: float = 0.0

    frequency: float = 0.0


# ==========================================================
# POWER
# ==========================================================

@dataclass
class Power:

    dynamic: float = 0.0

    leakage: float = 0.0


# ==========================================================
# DESIGN DATABASE
# ==========================================================

@dataclass
class Design:

    top: str = ""

    modules: List[Module] = field(default_factory=list)

    floorplan: Optional[Floorplan] = None

    placement: Optional[Placement] = None

    routing: Optional[Routing] = None

    timing: Optional[Timing] = None

    power: Optional[Power] = None

    metadata: Dict = field(default_factory=dict)