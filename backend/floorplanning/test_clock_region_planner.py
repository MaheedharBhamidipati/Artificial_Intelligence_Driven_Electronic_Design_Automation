from backend.floorplanning.models import Chip, Macro, MacroNet, MacroNetlist
from backend.floorplanning.clock_region_planner import ClockRegionPlanner


def make_macro(name, macro_type, x, y, w=10, h=10, cells=None):
    return Macro(name=name, macro_type=macro_type, x=x, y=y, width=w, height=h, cells=cells or [])


def make_chip(macros):
    chip = Chip(width=100, height=100, core_margin=8)
    chip.macros = macros
    return chip


# ==========================================================
# NO CONNECTIVITY
# ==========================================================

def test_no_macro_netlist_gives_empty_plan():

    chip = make_chip([make_macro("a", "Logic", 0, 0)])
    chip.macro_netlist = None

    plan = ClockRegionPlanner(chip).plan()

    assert plan.regions == []
    assert plan.unrouted_clock_nets == []


def test_no_clock_nets_gives_empty_plan():

    chip = make_chip([
        make_macro("a", "Logic", 0, 0),
        make_macro("b", "Logic", 20, 0),
    ])
    chip.macro_netlist = MacroNetlist(nets=[
        MacroNet(name="d1", kind="data", macros=["a", "b"], weight=1.0)
    ])

    plan = ClockRegionPlanner(chip).plan()

    assert plan.regions == []


# ==========================================================
# REGION GEOMETRY
# ==========================================================

def test_clock_net_produces_bounding_box_region():

    chip = make_chip([
        make_macro("Sequential Block", "Sequential", 10, 10, w=10, h=10, cells=["c1", "c2"]),
        make_macro("Memory Block", "Memory", 40, 25, w=15, h=15, cells=["c3"]),
    ])
    chip.macro_netlist = MacroNetlist(nets=[
        MacroNet(
            name="clk",
            kind="clock",
            macros=["Sequential Block", "Memory Block"],
            weight=2.0,
        )
    ])

    plan = ClockRegionPlanner(chip).plan()

    assert len(plan.regions) == 1

    region = plan.regions[0]

    assert region.clock_net == "clk"
    assert sorted(region.macros) == ["Memory Block", "Sequential Block"]

    # bounding box must fully contain both macros
    assert region.x <= 10
    assert region.y <= 10
    assert region.x + region.width >= 55
    assert region.y + region.height >= 40


def test_root_macro_is_the_one_with_more_cells():

    chip = make_chip([
        make_macro("Sequential Block", "Sequential", 10, 10, cells=["c1", "c2", "c3"]),
        make_macro("Memory Block", "Memory", 40, 25, cells=["c4"]),
    ])
    chip.macro_netlist = MacroNetlist(nets=[
        MacroNet(name="clk", kind="clock", macros=["Sequential Block", "Memory Block"], weight=2.0)
    ])

    plan = ClockRegionPlanner(chip).plan()

    assert plan.regions[0].root_macro == "Sequential Block"


def test_clock_net_touching_one_macro_is_unrouted():

    chip = make_chip([make_macro("Sequential Block", "Sequential", 10, 10, cells=["c1"])])
    chip.macro_netlist = MacroNetlist(nets=[
        MacroNet(name="clk", kind="clock", macros=["Sequential Block"], weight=1.0)
    ])

    plan = ClockRegionPlanner(chip).plan()

    assert plan.regions == []
    assert plan.unrouted_clock_nets == ["clk"]


def test_multiple_clock_nets_produce_multiple_regions():

    chip = make_chip([
        make_macro("Sequential Block", "Sequential", 10, 10, cells=["c1"]),
        make_macro("Memory Block", "Memory", 40, 25, cells=["c2"]),
        make_macro("Arithmetic Block", "Arithmetic", 60, 5, cells=["c3"]),
    ])
    chip.macro_netlist = MacroNetlist(nets=[
        MacroNet(name="clk_a", kind="clock", macros=["Sequential Block", "Memory Block"], weight=1.0),
        MacroNet(name="clk_b", kind="clock", macros=["Memory Block", "Arithmetic Block"], weight=1.0),
    ])

    plan = ClockRegionPlanner(chip).plan()

    assert len(plan.regions) == 2
    assert {r.clock_net for r in plan.regions} == {"clk_a", "clk_b"}
