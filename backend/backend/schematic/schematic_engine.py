import sys
import os

# Add backend root to path
BACKEND_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)


from backend.rtl_parser_engine.netlist_generator import NetlistGenerator

from backend.schematic.layout_engine import LayoutEngine
from backend.schematic.wire_router import WireRouter
from backend.schematic.svg_renderer import SVGRenderer


class SchematicGenerator:

    def __init__(self, filepath):
        self.filepath = filepath

    def generate(self):

        netlist_gen = NetlistGenerator(self.filepath)
        netlist = netlist_gen.generate()

        gates = netlist["gates"]

        layout_engine = LayoutEngine()
        positioned_gates = layout_engine.generate_layout(gates)

        router = WireRouter()
        wires = router.generate_wires(positioned_gates)

        renderer = SVGRenderer()

        for gate in positioned_gates:
            renderer.draw_gate(gate)

        renderer.draw_wires(wires)

        renderer.save()


if __name__ == "__main__":

    generator = SchematicGenerator(
        r"D:\AI_EDA_TOOL\backend\rtl_parser_engine\example.v"
    )

    generator.generate()
