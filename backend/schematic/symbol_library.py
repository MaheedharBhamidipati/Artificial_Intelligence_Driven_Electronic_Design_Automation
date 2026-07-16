"""
Symbol library: gate footprints (dimensions) and pin geometry.

This module is the single source of truth for how big a gate symbol is
and where its pins sit relative to the gate's (x, y) top-left corner.
Both the layout engine (for spacing/sizing) and the wire router (for
pin coordinates) depend on this module — gate sizing must not be
duplicated or hardcoded anywhere else.
"""

from typing import Dict, List, NamedTuple, Tuple


# (width, height) in SVG user units, keyed by gate type (upper-case).
_DIMENSIONS: Dict[str, Tuple[int, int]] = {
    "AND": (80, 40),
    "OR": (80, 40),
    "NAND": (80, 40),
    "NOR": (80, 40),
    "XOR": (80, 60),
    "XNOR": (80, 60),
    "NOT": (60, 40),
    "ADD": (100, 60),
    "SUB": (100, 60),
    "MUL": (100, 70),
    "BUFFER": (60, 40),
    "COMPARATOR": (100, 60),
    "MUX": (90, 70),
    "DFF": (100, 80),
    "FF": (100, 80),
    "REGISTER": (110, 80),
    "LATCH": (100, 80),
    "INPUT_PORT": (50, 30),
    "OUTPUT_PORT": (50, 30),
}

_DEFAULT_DIMENSIONS: Tuple[int, int] = (90, 60)

# Extra vertical spacing (px) reserved per input pin so gates with many
# fan-in pins still render with legible, non-overlapping pin spacing.
PIN_SPACING = 16
MIN_PIN_MARGIN = 12


class Pin(NamedTuple):
    x: int
    y: int


def gate_dimensions(gate_type: str) -> Tuple[int, int]:
    """Return (width, height) for a gate type. Unknown types get a sane
    default box rather than raising — new synthesis primitives show up
    regularly and shouldn't break layout."""
    return _DIMENSIONS.get((gate_type or "").upper(), _DEFAULT_DIMENSIONS)


def required_height_for_inputs(gate_type: str, num_inputs: int) -> int:
    """Gates with many fan-in pins (e.g. wide MUX/REGISTER buses) may need
    more height than the static footprint. Layout should use this instead
    of the raw dimension when spacing rows."""
    _, base_height = gate_dimensions(gate_type)
    needed = MIN_PIN_MARGIN * 2 + max(0, num_inputs - 1) * PIN_SPACING
    return max(base_height, needed)


def input_pin_positions(gate_type: str, num_inputs: int) -> List[Pin]:
    """Pin coordinates relative to the gate's top-left corner (0, 0),
    evenly distributed down the left edge."""
    if num_inputs <= 0:
        return []

    height = required_height_for_inputs(gate_type, num_inputs)

    if num_inputs == 1:
        return [Pin(0, height // 2)]

    usable = height - 2 * MIN_PIN_MARGIN
    step = usable / (num_inputs - 1)
    return [Pin(0, int(MIN_PIN_MARGIN + i * step)) for i in range(num_inputs)]


def output_pin_position(gate_type: str) -> Pin:
    """Single output pin, vertically centered on the right edge."""
    width, height = gate_dimensions(gate_type)
    return Pin(width, height // 2)


def clock_pin_position(gate_type: str) -> Pin:
    """Clock pin for sequential elements, centered on the bottom edge."""
    width, height = gate_dimensions(gate_type)
    return Pin(width // 2, height)
