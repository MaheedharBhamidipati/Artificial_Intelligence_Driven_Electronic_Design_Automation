"""
Entry point for the custom (non-Yosys) schematic pipeline:
netlist -> LayoutEngine -> WireRouter -> SVGRenderer.

For arbitrary/complex synthesized RTL, prefer
schematic_generator.generate_schematic (Yosys + Graphviz), which is the
more battle-tested path. This module renders directly from
NetlistGenerator output using AIDEA's own gate symbols, and is the
right entry point when you want the custom-styled schematic rather than
Graphviz's default node/edge look.

Fixes vs. the original implementation:
- No more sys.path hacking with a bare os.path.join — uses pathlib and
  resolves the backend root deterministically.
- No hardcoded Windows dev-machine path (D:\\AI_EDA_TOOL\\...) in the
  __main__ block — takes a CLI argument instead.
- Real error handling: missing input file, empty netlist, and pipeline
  failures are caught and reported instead of raising an unhandled
  traceback all the way to the caller.
"""

import argparse
import logging
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from backend.rtl_parser_engine.netlist_generator import NetlistGenerator
from backend.schematic.layout_engine import LayoutEngine
from backend.schematic.wire_router import WireRouter
from backend.schematic.svg_renderer import SVGRenderer

logger = logging.getLogger("aidea.schematic.schematic_engine")
if not logger.handlers:
    _handler = logging.StreamHandler(sys.stdout)
    _handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)


class SchematicGenerator:
    """Generates a custom-rendered SVG schematic for a single Verilog file."""

    def __init__(self, filepath: str, output_path: str = None):
        self.filepath = Path(filepath)
        self.output_path = Path(output_path) if output_path else self.filepath.with_suffix(".svg")

    def generate(self) -> str:
        if not self.filepath.exists():
            raise FileNotFoundError(f"Verilog source not found: {self.filepath}")

        logger.info("Parsing netlist from %s", self.filepath)
        netlist_gen = NetlistGenerator(str(self.filepath))
        netlist = netlist_gen.generate()

        gates = netlist.get("gates", [])
        if not gates:
            raise ValueError("Netlist contains no gates — nothing to render.")

        logger.info("Laying out %d gate(s)", len(gates))
        positioned_gates = LayoutEngine().generate_layout(gates)

        logger.info("Routing wires")
        wires = WireRouter().generate_wires(positioned_gates)

        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        renderer = SVGRenderer(filename=str(self.output_path))

        for gate in positioned_gates:
            renderer.draw_gate(gate)
        renderer.draw_wires(wires)

        saved_path = renderer.save()
        logger.info("Schematic written to %s", saved_path)
        return saved_path


def _parse_args():
    parser = argparse.ArgumentParser(description="Generate an SVG schematic from a Verilog file.")
    parser.add_argument("verilog_file", help="Path to the input .v file")
    parser.add_argument("-o", "--output", help="Output SVG path (default: alongside input)", default=None)
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    try:
        SchematicGenerator(args.verilog_file, args.output).generate()
    except Exception as exc:
        logger.error("Schematic generation failed: %s", exc)
        sys.exit(1)
