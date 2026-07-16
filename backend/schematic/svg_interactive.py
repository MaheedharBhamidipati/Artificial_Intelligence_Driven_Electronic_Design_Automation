"""
Interactive metadata + client-side behavior for SVG schematics.

Attaches data-* attributes to gate elements so a frontend can wire up
click/hover handlers (highlight fanout, show a properties panel, etc.)
without re-parsing the SVG, and provides an optional CSS/JS snippet for
basic hover highlighting with no framework required.
"""

import logging

logger = logging.getLogger("aidea.schematic.svg_interactive")


def add_metadata(svg_element, gate: dict):
    """Attach data-* attributes describing a gate to an svgwrite element.

    Tolerant of missing keys: a gate dict may legitimately have no
    inputs (a primary input port) or no output (a primary output port).
    The original implementation indexed gate["gate_id"] / gate["output"]
    / gate["inputs"] directly, which raised KeyError and aborted the
    entire render the first time a port-only gate showed up.
    """
    attrs = {
        "class": "schematic-gate",
        "data-gate-id": gate.get("gate_id", gate.get("id", "")),
        "data-gate-type": gate.get("gate_type", ""),
        "data-output": gate.get("output") or "",
        "data-inputs": ",".join(gate.get("inputs", []) or []),
    }
    try:
        svg_element.update(attrs)
    except Exception:
        logger.warning("Failed to attach interactive metadata to SVG element", exc_info=True)
    return svg_element


def embed_interactivity_style() -> str:
    """CSS/JS block for hover highlighting of gates, keyed off the
    data-gate-id attribute set by add_metadata(). Meant to be inlined
    just before </svg>."""
    return """
<style>
.schematic-gate { cursor: pointer; transition: filter 0.15s ease; }
.schematic-gate:hover { filter: brightness(1.15); stroke-width: 3; }
</style>
<script><![CDATA[
document.querySelectorAll('.schematic-gate').forEach(function (el) {
  el.addEventListener('click', function () {
    var id = el.getAttribute('data-gate-id');
    document.dispatchEvent(new CustomEvent('schematic:gate-click', { detail: { gateId: id } }));
  });
});
]]></script>
"""


def inject_interactivity(svg_text: str) -> str:
    """Insert the interactivity style/script block into raw SVG text
    right before the closing tag. No-op if the SVG is malformed/missing
    a closing tag, rather than raising."""
    if "</svg>" not in svg_text:
        logger.warning("inject_interactivity: no </svg> tag found, leaving SVG unmodified")
        return svg_text
    return svg_text.replace("</svg>", embed_interactivity_style() + "</svg>")
