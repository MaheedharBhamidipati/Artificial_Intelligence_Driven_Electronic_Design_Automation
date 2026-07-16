import sys, logging
from pathlib import Path


def _find_project_root(start: Path) -> Path:
    """Walk upward from this file looking for a directory that contains
    a 'backend' package — works whether this script sits at the project
    root (D:\\AI_EDA_TOOL\\test_pipeline.py) or alongside the modules it's
    testing (D:\\AI_EDA_TOOL\\backend\\schematic\\test_pipeline.py)."""
    for candidate in [start, *start.parents]:
        if (candidate / "backend").is_dir():
            return candidate
    raise RuntimeError(
        f"Could not find a 'backend' directory above {start}. "
        "Place this script inside your AIDEA project tree "
        "(anywhere at or under D:\\AI_EDA_TOOL)."
    )


PROJECT_ROOT = _find_project_root(Path(__file__).resolve().parent)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO)

from backend.schematic.layout_engine import LayoutEngine
from backend.schematic.wire_router import WireRouter
from backend.schematic.svg_renderer import SVGRenderer
from backend.schematic import bus_router, ff_renderer, symbol_library

# Synthetic netlist deliberately containing:
# - a primary input feeding two gates (fan-out)
# - a bus signal data[7:0]
# - a DFF closing a combinational feedback loop (this is what silently
#   dropped gates in the ORIGINAL layout_engine.py)
# - a gate with 3 inputs, to test pin spacing
gates = [
    {"id": "u_and1", "gate_type": "AND", "inputs": ["a", "b"], "output": "n1"},
    {"id": "u_xor1", "gate_type": "XOR", "inputs": ["n1", "data[7:0]"], "output": "n2"},
    {"id": "u_dff1", "gate_type": "DFF", "inputs": ["n2", "clk"], "output": "q1"},
    # feedback: q1 feeds back into u_and1's sibling gate, closing a loop
    {"id": "u_or1", "gate_type": "OR", "inputs": ["q1", "a", "b"], "output": "n1_alt"},
    {"id": "u_mux1", "gate_type": "MUX", "inputs": ["q1", "n1_alt", "sel"], "output": "out"},
    # cyclic-looking dependency purely for stress-testing cycle breaking:
    {"id": "u_not1", "gate_type": "NOT", "inputs": ["out"], "output": "fb1"},
]
# Deliberately make u_and1 depend indirectly on fb1 to create a real cycle
gates[0]["inputs"] = ["a", "fb1"]

layout = LayoutEngine().generate_layout(gates)
print(f"\nPositioned {len(layout)} / {len(gates)} gates:")
for g in layout:
    print(f"  {g['id']:10s} type={g['gate_type']:6s} x={g['x']:4d} y={g['y']:4d} w={g['width']:3d} h={g['height']:3d}")

assert len(layout) == len(gates), "BUG: gates were dropped!"

wires = WireRouter().generate_wires(layout)
print(f"\nRouted {len(wires)} wires:")
for w in wires:
    tag = "BUS " if w["is_bus"] else ("FB  " if w["is_feedback"] else "    ")
    print(f"  {tag}{w['signal']:12s} points={w['points']}")

renderer = SVGRenderer(filename=str(Path(__file__).resolve().parent / "test_output.svg"))
for g in layout:
    renderer.draw_gate(g)
renderer.draw_wires(wires)
path = renderer.save()
print(f"\nSaved: {path}")

# sanity checks on helper modules
assert bus_router.is_bus("data[7:0]") is True
assert bus_router.is_bus("clk") is False
assert bus_router.bus_width("data[7:0]") == 8
assert ff_renderer.is_sequential_gate("DFF") is True
assert ff_renderer.clock_input_index({"inputs": ["n2", "clk"]}) == 1
assert symbol_library.gate_dimensions("DFF") == (100, 80)
print("\nAll assertions passed.")
