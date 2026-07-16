from backend.floorplanning.models import Chip, Macro, MacroNet, MacroNetlist, StandardCellRegion
from backend.floorplanning.timing_driven_floorplanner import TimingDrivenFloorplanner


def make_macro(name, macro_type, x, y, w=10, h=10, fixed=False):
    return Macro(name=name, macro_type=macro_type, x=x, y=y, width=w, height=h, fixed=fixed)


def make_chip(macros, width=100, height=100, core_margin=8):
    chip = Chip(width=width, height=height, core_margin=core_margin)
    chip.macros = macros
    chip.standard_cells = StandardCellRegion(
        x=core_margin, y=core_margin, width=width - 2 * core_margin, height=12
    )
    return chip


# ==========================================================
# NO-OP CASES
# ==========================================================

def test_no_macro_netlist_is_a_noop():

    chip = make_chip([
        make_macro("a", "Logic", 10, 30),
        make_macro("b", "Logic", 70, 30),
    ])
    chip.macro_netlist = None

    before = [(m.x, m.y) for m in chip.macros]

    chip = TimingDrivenFloorplanner(chip).optimize()

    after = [(m.x, m.y) for m in chip.macros]

    assert before == after


def test_empty_nets_is_a_noop():

    chip = make_chip([
        make_macro("a", "Logic", 10, 30),
        make_macro("b", "Logic", 70, 30),
    ])
    chip.macro_netlist = MacroNetlist(nets=[])

    before = [(m.x, m.y) for m in chip.macros]

    chip = TimingDrivenFloorplanner(chip).optimize()

    after = [(m.x, m.y) for m in chip.macros]

    assert before == after


# ==========================================================
# CONNECTED MACROS MOVE CLOSER
# ==========================================================

def test_connected_macros_move_closer_together():

    chip = make_chip([
        make_macro("a", "Logic", 10, 30),
        make_macro("b", "Logic", 75, 30),
    ])
    chip.macro_netlist = MacroNetlist(nets=[
        MacroNet(name="n1", kind="data", macros=["a", "b"], weight=5.0)
    ])

    def center_distance():
        a, b = chip.macros
        acx, acy = a.x + a.width / 2, a.y + a.height / 2
        bcx, bcy = b.x + b.width / 2, b.y + b.height / 2
        return ((acx - bcx) ** 2 + (acy - bcy) ** 2) ** 0.5

    before = center_distance()

    chip = TimingDrivenFloorplanner(chip).optimize()

    after = center_distance()

    assert after < before


def test_fixed_macro_does_not_move():

    chip = make_chip([
        make_macro("a", "Logic", 10, 30, fixed=True),
        make_macro("b", "Logic", 75, 30),
    ])
    chip.macro_netlist = MacroNetlist(nets=[
        MacroNet(name="n1", kind="data", macros=["a", "b"], weight=5.0)
    ])

    chip = TimingDrivenFloorplanner(chip).optimize()

    assert chip.macros[0].x == 10
    assert chip.macros[0].y == 30


def test_macros_stay_non_overlapping_after_refinement():

    chip = make_chip([
        make_macro("a", "Logic", 10, 30),
        make_macro("b", "Logic", 25, 30),
        make_macro("c", "Logic", 40, 30),
    ])
    chip.macro_netlist = MacroNetlist(nets=[
        MacroNet(name="n1", kind="data", macros=["a", "b", "c"], weight=3.0)
    ])

    chip = TimingDrivenFloorplanner(chip).optimize()

    from backend.floorplanning.utils import overlap

    macros = chip.macros
    for i in range(len(macros)):
        for j in range(i + 1, len(macros)):
            assert not overlap(macros[i], macros[j])


def test_macros_stay_within_core_bounds():

    chip = make_chip([
        make_macro("a", "Logic", 10, 30),
        make_macro("b", "Logic", 85, 30),
    ])
    chip.macro_netlist = MacroNetlist(nets=[
        MacroNet(name="n1", kind="data", macros=["a", "b"], weight=8.0)
    ])

    chip = TimingDrivenFloorplanner(chip).optimize()

    for m in chip.macros:
        assert m.x >= chip.core_margin - 1e-6
        assert m.x + m.width <= chip.width - chip.core_margin + 1e-6


# ==========================================================
# WEIGHTED HPWL
# ==========================================================

def test_weighted_hpwl_none_without_netlist():

    chip = make_chip([make_macro("a", "Logic", 10, 30)])
    chip.macro_netlist = None

    assert TimingDrivenFloorplanner.estimate_weighted_hpwl(chip) is None


def test_weighted_hpwl_scales_with_weight():

    chip = make_chip([
        make_macro("a", "Logic", 0, 0, w=10, h=10),
        make_macro("b", "Logic", 30, 0, w=10, h=10),
    ])
    chip.macro_netlist = MacroNetlist(nets=[
        MacroNet(name="n1", kind="data", macros=["a", "b"], weight=2.0)
    ])

    hpwl = TimingDrivenFloorplanner.estimate_weighted_hpwl(chip)

    # center-to-center x distance is 30, y distance is 0 -> hpwl=30, * weight 2 = 60
    assert hpwl == 60.0
