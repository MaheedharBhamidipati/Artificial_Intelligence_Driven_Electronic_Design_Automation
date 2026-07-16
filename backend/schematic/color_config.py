"""
Central color/style configuration for schematic rendering.

All colors are defined once here so the renderer, interactive layer, and
any future theming code stay in sync. Do not hardcode colors anywhere
else in the schematic package.
"""

from dataclasses import dataclass, field
from typing import Dict


# ---------------------------------------------------------------------------
# Base palette (kept as flat constants for backward compatibility with any
# code importing the original names directly)
# ---------------------------------------------------------------------------

BACKGROUND_COLOR = "#FFFFFF"
TEXT_COLOR = "#111827"
GRID_COLOR = "#E5E7EB"

BLOCK_COLOR = "#4A90E2"          # default gate fill
BLOCK_STROKE_COLOR = "#1E3A5F"
WIRE_COLOR = "#00AA00"           # default single-bit wire color
BUS_WIRE_COLOR = "#B45309"       # multi-bit bus wire color (thicker, distinct)
FEEDBACK_WIRE_COLOR = "#DC2626"  # sequential feedback / cycle-broken nets

INPUT_COLOR = "#FFD700"
OUTPUT_COLOR = "#FFA500"

SELECTION_COLOR = "#2563EB"
HOVER_COLOR = "#60A5FA"

# Per-gate-type fill colors. Falls back to BLOCK_COLOR if a type is missing,
# so new/unrecognized synthesis primitives never break rendering.
GATE_COLORS: Dict[str, str] = {
    "AND": "#4A90E2",
    "OR": "#4A90E2",
    "XOR": "#7C3AED",
    "NAND": "#4A90E2",
    "NOR": "#4A90E2",
    "XNOR": "#7C3AED",
    "NOT": "#94A3B8",
    "BUFFER": "#94A3B8",
    "ADD": "#059669",
    "SUB": "#059669",
    "MUL": "#059669",
    "COMPARATOR": "#0891B2",
    "MUX": "#D97706",
    "DFF": "#DC2626",
    "FF": "#DC2626",
    "REGISTER": "#DC2626",
    "LATCH": "#B91C1C",
    "INPUT_PORT": INPUT_COLOR,
    "OUTPUT_PORT": OUTPUT_COLOR,
}


def gate_color(gate_type: str) -> str:
    """Return the fill color for a gate type, defaulting to BLOCK_COLOR."""
    return GATE_COLORS.get((gate_type or "").upper(), BLOCK_COLOR)


@dataclass(frozen=True)
class Theme:
    """Bundled theme. Not wired up everywhere yet, but gives us a single
    place to add light/dark or user-selectable themes later without
    touching every renderer call site."""

    background: str = BACKGROUND_COLOR
    text: str = TEXT_COLOR
    grid: str = GRID_COLOR
    block: str = BLOCK_COLOR
    block_stroke: str = BLOCK_STROKE_COLOR
    wire: str = WIRE_COLOR
    bus_wire: str = BUS_WIRE_COLOR
    feedback_wire: str = FEEDBACK_WIRE_COLOR
    selection: str = SELECTION_COLOR
    hover: str = HOVER_COLOR
    gate_colors: Dict[str, str] = field(default_factory=lambda: dict(GATE_COLORS))


DEFAULT_THEME = Theme()
