"""
Bus-signal utilities.

RTL signals representing multi-bit buses use Verilog-style range
notation, e.g. "data[7:0]" or "addr[31:0]". This module centralizes
parsing so the layout, routing, and rendering layers all agree on what
counts as a bus and how wide it is, instead of each doing its own
ad-hoc string check.
"""

import re
from dataclasses import dataclass
from typing import Optional

_BUS_PATTERN = re.compile(r"^(?P<base>[A-Za-z_][A-Za-z0-9_]*)\[(?P<msb>\d+):(?P<lsb>\d+)\]$")
_BIT_PATTERN = re.compile(r"^(?P<base>[A-Za-z_][A-Za-z0-9_]*)\[(?P<bit>\d+)\]$")


@dataclass(frozen=True)
class BusInfo:
    base_name: str
    msb: int
    lsb: int

    @property
    def width(self) -> int:
        return abs(self.msb - self.lsb) + 1


def is_bus(signal: str) -> bool:
    """True if the signal carries a Verilog-style range, e.g. data[7:0].
    A single indexed bit like sel[2] is NOT a bus on its own — use
    is_bus_bit() for that case."""
    if not signal:
        return False
    return bool(_BUS_PATTERN.match(signal.strip()))


def is_bus_bit(signal: str) -> bool:
    """True if this is a single indexed bit of a bus, e.g. addr[3]."""
    if not signal:
        return False
    return bool(_BIT_PATTERN.match(signal.strip()))


def parse_bus(signal: str) -> Optional[BusInfo]:
    """Parse 'name[msb:lsb]' into a BusInfo, or None if not a bus."""
    match = _BUS_PATTERN.match((signal or "").strip())
    if not match:
        return None
    return BusInfo(
        base_name=match.group("base"),
        msb=int(match.group("msb")),
        lsb=int(match.group("lsb")),
    )


def bus_width(signal: str) -> int:
    """Bit width of a signal; 1 for scalar/non-bus signals."""
    info = parse_bus(signal)
    return info.width if info else 1


def display_label(signal: str) -> str:
    """Label to render on the schematic for a signal. Currently a
    passthrough, but kept as a single seam so label formatting (e.g.
    truncating very wide buses) can change without touching callers."""
    return signal
