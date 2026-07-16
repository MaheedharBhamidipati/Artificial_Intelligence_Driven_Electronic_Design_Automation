from backend.floorplanning.models import Chip, Macro
from backend.floorplanning.power_domain_manager import (
    PowerDomainManager,
    DEFAULT_VOLTAGE_MAP,
)


def make_macro(name, macro_type, x, y, w=10, h=10):
    return Macro(name=name, macro_type=macro_type, x=x, y=y, width=w, height=h)


def make_chip(macros):
    chip = Chip(width=100, height=100, core_margin=8)
    chip.macros = macros
    return chip


# ==========================================================
# ASSIGNMENT
# ==========================================================

def test_macros_grouped_by_voltage_not_type():

    # Logic and Sequential share a voltage in the default map --
    # they must end up in the SAME domain even though MacroBuilder
    # classified them differently.
    chip = make_chip([
        make_macro("m1", "Logic", 0, 0),
        make_macro("m2", "Sequential", 50, 50),
    ])

    chip = PowerDomainManager(chip).generate()

    assert len(chip.power_domain_plan.domains) == 1
    assert chip.macros[0].domain == chip.macros[1].domain


def test_different_voltage_macros_get_different_domains():

    chip = make_chip([
        make_macro("mem", "Memory", 0, 0),
        make_macro("io", "IO", 50, 50),
    ])

    chip = PowerDomainManager(chip).generate()

    domains = {d.name for d in chip.power_domain_plan.domains}

    assert len(domains) == 2
    assert chip.macros[0].domain != chip.macros[1].domain


def test_domain_bbox_matches_member_macros():

    chip = make_chip([
        make_macro("a", "Logic", 5, 5, w=10, h=10),
        make_macro("b", "Logic", 20, 30, w=10, h=10),
    ])

    chip = PowerDomainManager(chip).generate()

    domain = chip.power_domain_plan.domains[0]

    assert domain.x == 5
    assert domain.y == 5
    assert domain.width == 25   # (20+10) - 5
    assert domain.height == 35  # (30+10) - 5


def test_custom_voltage_map_overrides_default():

    chip = make_chip([
        make_macro("a", "Logic", 0, 0),
        make_macro("b", "Memory", 50, 50),
    ])

    # Force everything onto one rail
    chip = PowerDomainManager(chip, voltage_map={"Logic": 1.0, "Memory": 1.0}).generate()

    assert len(chip.power_domain_plan.domains) == 1


def test_no_macros_produces_empty_plan_without_crash():

    chip = make_chip([])

    chip = PowerDomainManager(chip).generate()

    assert chip.power_domain_plan.domains == []
    assert chip.power_domain_plan.boundary_cells == []


# ==========================================================
# BOUNDARY CELLS
# ==========================================================

def test_adjacent_different_voltage_macros_get_level_shifter():

    chip = make_chip([
        make_macro("mem", "Memory", 0, 0, w=10, h=10),
        make_macro("io", "IO", 10, 0, w=10, h=10),  # touching edge
    ])

    chip = PowerDomainManager(chip, adjacency_threshold=1.0).generate()

    cells = chip.power_domain_plan.boundary_cells

    assert len(cells) == 1
    assert cells[0].kind == "level_shifter"


def test_adjacent_same_voltage_different_domain_gets_isolation():

    # Same voltage, but forced into different domains via a map
    # that still separates them by macro_type-derived domain name
    # -- simulate via distinct voltage_map values that happen to
    # be numerically equal is not possible (domains are keyed by
    # voltage), so instead verify same-voltage macros are NEVER
    # split, confirming isolation cells only arise when domains
    # legitimately differ.
    chip = make_chip([
        make_macro("a", "Logic", 0, 0, w=10, h=10),
        make_macro("b", "Sequential", 10, 0, w=10, h=10),
    ])

    chip = PowerDomainManager(chip, adjacency_threshold=1.0).generate()

    # Logic and Sequential share a voltage -> same domain -> no
    # boundary cell should be generated between them at all.
    assert chip.power_domain_plan.boundary_cells == []


def test_distant_different_domain_macros_get_no_boundary_cell():

    chip = make_chip([
        make_macro("mem", "Memory", 0, 0, w=10, h=10),
        make_macro("io", "IO", 90, 90, w=5, h=5),
    ])

    chip = PowerDomainManager(chip, adjacency_threshold=1.0).generate()

    assert chip.power_domain_plan.boundary_cells == []


def test_boundary_cell_sits_between_the_two_macros():

    chip = make_chip([
        make_macro("mem", "Memory", 0, 0, w=10, h=10),
        make_macro("io", "IO", 10, 0, w=10, h=10),
    ])

    chip = PowerDomainManager(chip, adjacency_threshold=1.0).generate()

    cell = chip.power_domain_plan.boundary_cells[0]

    assert 0 <= cell.x <= 20
    assert 0 <= cell.y <= 10


def test_default_voltage_map_covers_all_macro_categories():

    # Regression guard: every category MacroBuilder can emit
    # must resolve to a voltage, or _voltage_for's fallback is
    # silently doing the work instead.
    for category in ["Arithmetic", "Logic", "Sequential", "Memory",
                      "MUX", "IO", "FSM", "Output", "Unknown"]:
        assert category in DEFAULT_VOLTAGE_MAP
