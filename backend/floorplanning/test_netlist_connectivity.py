from backend.floorplanning.models import Macro
from backend.floorplanning.design import Module, Cell, Net
from backend.floorplanning.netlist_connectivity import (
    NetlistConnectivity,
    _classify_net,
)


def make_macro(name, macro_type, cells):
    return Macro(name=name, macro_type=macro_type, cells=cells)


def make_module(cells, nets):
    return Module(name="top", cells=cells, nets=nets)


# ==========================================================
# BASIC CROSS-MACRO NET
# ==========================================================

def test_net_spanning_two_macros_is_recorded():

    # bit 5 is shared: c1 (macro A) drives it, c2 (macro B) reads it
    cells = [
        Cell(name="c1", cell_type="ADDER", connections={"Y": [5]}),
        Cell(name="c2", cell_type="$_DFF_P_", connections={"D": [5]}),
    ]
    nets = [Net(name="sum_net", bits=[5])]

    macros = [
        make_macro("Arithmetic Block", "Arithmetic", ["c1"]),
        make_macro("Sequential Block", "Sequential", ["c2"]),
    ]

    module = make_module(cells, nets)

    netlist = NetlistConnectivity(module, macros).build()

    assert len(netlist.nets) == 1
    assert netlist.nets[0].name == "sum_net"
    assert sorted(netlist.nets[0].macros) == ["Arithmetic Block", "Sequential Block"]


def test_net_local_to_one_macro_is_dropped():

    # both cells sharing bit 9 live in the SAME macro -> no
    # macro-level net should be produced.
    cells = [
        Cell(name="c1", cell_type="ADDER", connections={"Y": [9]}),
        Cell(name="c2", cell_type="ADDER", connections={"A": [9]}),
    ]
    nets = [Net(name="local_net", bits=[9])]

    macros = [make_macro("Arithmetic Block", "Arithmetic", ["c1", "c2"])]

    netlist = NetlistConnectivity(make_module(cells, nets), macros).build()

    assert netlist.nets == []


def test_weight_counts_cells_not_bits():

    # a 2-bit bus (bits 1,2) between the same pair of cells should
    # count once per cell, not once per bit.
    cells = [
        Cell(name="c1", cell_type="ADDER", connections={"Y": [1, 2]}),
        Cell(name="c2", cell_type="$_DFF_P_", connections={"D": [1, 2]}),
    ]
    nets = [Net(name="bus_net", bits=[1, 2])]

    macros = [
        make_macro("Arithmetic Block", "Arithmetic", ["c1"]),
        make_macro("Sequential Block", "Sequential", ["c2"]),
    ]

    netlist = NetlistConnectivity(make_module(cells, nets), macros).build()

    assert len(netlist.nets) == 1
    assert netlist.nets[0].weight == 2.0  # one pin-count per cell (2 cells)


def test_no_module_returns_empty_netlist():

    macros = [make_macro("Logic Block", "Logic", ["c1"])]

    netlist = NetlistConnectivity(None, macros).build()

    assert netlist.nets == []


# ==========================================================
# NET KIND CLASSIFICATION
# ==========================================================

def test_classify_net_detects_clock():
    assert _classify_net("clk") == "clock"
    assert _classify_net("sys_clock_i") == "clock"


def test_classify_net_detects_reset():
    assert _classify_net("rst_n") == "reset"


def test_classify_net_defaults_to_data():
    assert _classify_net("din_3") == "data"


def test_clock_net_spanning_macros_is_classified_clock():

    cells = [
        Cell(name="c1", cell_type="RAM", connections={"CLK": [4]}),
        Cell(name="c2", cell_type="$_DFF_P_", connections={"CLK": [4]}),
    ]
    nets = [Net(name="clk", bits=[4])]

    macros = [
        make_macro("Memory Block", "Memory", ["c1"]),
        make_macro("Sequential Block", "Sequential", ["c2"]),
    ]

    netlist = NetlistConnectivity(make_module(cells, nets), macros).build()

    assert len(netlist.nets) == 1
    assert netlist.nets[0].kind == "clock"
    assert netlist.clock_nets[0].name == "clk"
