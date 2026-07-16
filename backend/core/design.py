"""
============================================================

AIDEA Core Design Database

============================================================
"""

from dataclasses import dataclass, field

from typing import Dict, List


# ==========================================================

@dataclass
class Port:

    name: str

    direction: str

    bits: List[int] = field(default_factory=list)


# ==========================================================

@dataclass
class Net:

    name: str

    bits: List[int] = field(default_factory=list)


# ==========================================================

@dataclass
class Cell:

    name: str

    cell_type: str

    connections: Dict = field(default_factory=dict)


# ==========================================================

@dataclass
class Module:

    name: str

    ports: List[Port] = field(default_factory=list)

    cells: List[Cell] = field(default_factory=list)

    nets: List[Net] = field(default_factory=list)


# ==========================================================

@dataclass
class Design:

    top: str = ""

    modules: List[Module] = field(default_factory=list)

    metadata: Dict = field(default_factory=dict)