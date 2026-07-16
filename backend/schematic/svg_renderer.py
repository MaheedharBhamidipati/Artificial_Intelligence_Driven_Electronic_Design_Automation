"""
SVG rendering for RTL schematics.

Draws positioned gates (from LayoutEngine) and routed wires (from
WireRouter) into an svgwrite Drawing.

Fixes vs. the original implementation:
- Canvas size is computed from actual layout/wire extents instead of
  being hardcoded to 1600x1200 — any circuit bigger than that was
  previously clipped with no warning.
- Gate boxes use per-type dimensions and colors (symbol_library /
  color_config) instead of every gate rendering as an identical
  80x40 blue box regardless of type.
- Wires are drawn as full orthogonal polylines instead of a single
  straight segment, matching what WireRouter now actually produces.
- Bus and feedback nets are visually distinguished (thicker / colored).
"""

import logging
from typing import List

import svgwrite

from backend.schematic.color_config import (
    TEXT_COLOR,
    BACKGROUND_COLOR,
    BLOCK_STROKE_COLOR,
    WIRE_COLOR,
    BUS_WIRE_COLOR,
    FEEDBACK_WIRE_COLOR,
    gate_color,
)
from backend.schematic.svg_interactive import add_metadata

logger = logging.getLogger("aidea.schematic.svg_renderer")

_CANVAS_MARGIN = 80
_MIN_CANVAS_SIZE = (800, 600)


class SVGRenderer:
    """Renders a positioned, routed schematic to an SVG file.

    Gates and wires are buffered via draw_gate()/draw_wires() and the
    drawing itself is only built in save(), once the full extent of the
    layout is known — this is what lets the canvas size be computed
    correctly instead of guessed up front.
    """

    def __init__(self, filename: str = "schematic.svg"):
        self.filename = filename
        self._gates: List[dict] = []
        self._wires: List[dict] = []
        self.dwg = None

    def draw_gate(self, gate: dict) -> None:
        self._gates.append(gate)

    def draw_wires(self, wires: List[dict]) -> None:
        self._wires.extend(wires)

    # ------------------------------------------------------------------

    def _compute_canvas_size(self):
        max_x, max_y = _MIN_CANVAS_SIZE
        for gate in self._gates:
            max_x = max(max_x, gate["x"] + gate["width"])
            max_y = max(max_y, gate["y"] + gate["height"])
        for wire in self._wires:
            for (px, py) in wire.get("points", []):
                max_x = max(max_x, px)
                max_y = max(max_y, py)
        return max_x + _CANVAS_MARGIN, max_y + _CANVAS_MARGIN

    def _build_drawing(self):
        width, height = self._compute_canvas_size()
        # debug=False: svgwrite's default validator rejects data-* custom
        # attributes (used for click/hover metadata in svg_interactive.py)
        # with a ValueError. Turning off strict attribute validation is
        # required for that metadata to actually get attached instead of
        # silently failing on every single gate.
        dwg = svgwrite.Drawing(self.filename, size=(f"{width}px", f"{height}px"), debug=False)
        dwg.viewbox(0, 0, width, height)
        dwg.add(dwg.rect(insert=(0, 0), size=("100%", "100%"), fill=BACKGROUND_COLOR))
        return dwg

    def _render_gate(self, dwg, gate: dict) -> None:
        x, y = gate["x"], gate["y"]
        width, height = gate["width"], gate["height"]
        gate_type = gate.get("gate_type", "")

        rect = dwg.rect(
            insert=(x, y),
            size=(width, height),
            fill=gate_color(gate_type),
            stroke=BLOCK_STROKE_COLOR,
            stroke_width=2,
            rx=8,
            ry=8,
        )
        add_metadata(rect, gate)
        dwg.add(rect)

        label = gate.get("label") or gate_type
        dwg.add(
            dwg.text(
                label,
                insert=(x + width / 2, y + height / 2 + 5),
                fill=TEXT_COLOR,
                font_size="13px",
                font_family="Arial, sans-serif",
                text_anchor="middle",
            )
        )

        gate_id = gate.get("id")
        if gate_id:
            dwg.add(
                dwg.text(
                    str(gate_id),
                    insert=(x + 4, y + 12),
                    fill=TEXT_COLOR,
                    font_size="9px",
                    font_family="Arial, sans-serif",
                    opacity=0.6,
                )
            )

    def _render_wire(self, dwg, wire: dict) -> None:
        points = wire.get("points")
        if not points or len(points) < 2:
            logger.warning("Skipping wire with insufficient points: %r", wire.get("signal"))
            return

        if wire.get("is_feedback"):
            color = FEEDBACK_WIRE_COLOR
        elif wire.get("is_bus"):
            color = BUS_WIRE_COLOR
        else:
            color = WIRE_COLOR

        stroke_width = 4 if wire.get("is_bus") else 2

        dwg.add(dwg.polyline(points=points, fill="none", stroke=color, stroke_width=stroke_width))

        label_x, label_y = points[0][0] + 4, points[0][1] - 6
        dwg.add(
            dwg.text(
                wire.get("signal", ""),
                insert=(label_x, label_y),
                fill=TEXT_COLOR,
                font_size="10px",
                font_family="Arial, sans-serif",
            )
        )

    def save(self) -> str:
        self.dwg = self._build_drawing()

        for gate in self._gates:
            self._render_gate(self.dwg, gate)
        for wire in self._wires:
            self._render_wire(self.dwg, wire)

        self.dwg.save()
        logger.info("SVG schematic generated -> %s (%d gates, %d wires)",
                    self.filename, len(self._gates), len(self._wires))
        return self.filename
