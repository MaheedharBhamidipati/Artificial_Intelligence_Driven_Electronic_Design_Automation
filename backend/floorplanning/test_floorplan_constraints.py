from backend.floorplanning.models import (
    Chip, Macro,
    FixedMacroConstraint, RegionConstraint, GroupGuideConstraint,
)
from backend.floorplanning.floorplan_constraints import FloorplanConstraints


def make_chip():
    chip = Chip(width=100, height=100, core_margin=8)
    chip.macros = [
        Macro(name="a", macro_type="Logic", x=10, y=10, width=10, height=10),
        Macro(name="b", macro_type="Logic", x=40, y=40, width=10, height=10),
    ]
    return chip


# ==========================================================
# FIXED MACRO
# ==========================================================

def test_fixed_macro_moves_and_pins_macro():

    chip = make_chip()

    c = FixedMacroConstraint(macro_name="a", x=70, y=70)

    chip, violations = FloorplanConstraints(chip, [c]).apply()

    macro_a = next(m for m in chip.macros if m.name == "a")

    assert macro_a.x == 70
    assert macro_a.y == 70
    assert macro_a.fixed is True
    assert violations == []  # clearly separated from 'b' at (40,40)-(50,50)


def test_fixed_macro_unknown_name_reports_violation():

    chip = make_chip()

    c = FixedMacroConstraint(macro_name="ghost", x=0, y=0)

    chip, violations = FloorplanConstraints(chip, [c]).apply()

    assert len(violations) == 1
    assert "ghost" in violations[0]


def test_fixed_macro_overlap_reported():

    chip = make_chip()

    # Force 'a' directly on top of 'b'
    c = FixedMacroConstraint(macro_name="a", x=41, y=41)

    chip, violations = FloorplanConstraints(chip, [c]).apply()

    assert any("overlaps" in v for v in violations)


# ==========================================================
# REGION
# ==========================================================

def test_region_constraint_passes_when_macro_inside():

    chip = make_chip()

    c = RegionConstraint(name="r1", x=0, y=0, width=30, height=30, macro_names=["a"])

    chip, violations = FloorplanConstraints(chip, [c]).apply()

    assert violations == []


def test_region_constraint_flags_macro_outside():

    chip = make_chip()

    c = RegionConstraint(name="r1", x=0, y=0, width=20, height=20, macro_names=["b"])

    chip, violations = FloorplanConstraints(chip, [c]).apply()

    assert len(violations) == 1
    assert "r1" in violations[0]


def test_region_constraint_unknown_macro_reported():

    chip = make_chip()

    c = RegionConstraint(name="r1", x=0, y=0, width=20, height=20, macro_names=["ghost"])

    chip, violations = FloorplanConstraints(chip, [c]).apply()

    assert len(violations) == 1
    assert "ghost" in violations[0]


# ==========================================================
# GROUP GUIDE
# ==========================================================

def test_group_guide_within_span_passes():

    chip = make_chip()

    c = GroupGuideConstraint(name="g1", macro_names=["a", "b"], max_span=100)

    chip, violations = FloorplanConstraints(chip, [c]).apply()

    assert violations == []


def test_group_guide_exceeding_span_flagged():

    chip = make_chip()

    c = GroupGuideConstraint(name="g1", macro_names=["a", "b"], max_span=10)

    chip, violations = FloorplanConstraints(chip, [c]).apply()

    assert len(violations) == 1
    assert "g1" in violations[0]


def test_group_guide_without_max_span_never_flags():

    chip = make_chip()

    c = GroupGuideConstraint(name="g1", macro_names=["a", "b"])

    chip, violations = FloorplanConstraints(chip, [c]).apply()

    assert violations == []


# ==========================================================
# from_dicts
# ==========================================================

def test_from_dicts_builds_all_three_kinds():

    specs = [
        {"kind": "fixed_macro", "macro_name": "a", "x": 1, "y": 2},
        {"kind": "region", "name": "r1", "x": 0, "y": 0, "width": 10, "height": 10},
        {"kind": "group_guide", "name": "g1", "macro_names": ["a", "b"]},
    ]

    objs = FloorplanConstraints.from_dicts(specs)

    assert isinstance(objs[0], FixedMacroConstraint)
    assert isinstance(objs[1], RegionConstraint)
    assert isinstance(objs[2], GroupGuideConstraint)


def test_from_dicts_unknown_kind_raises():

    try:
        FloorplanConstraints.from_dicts([{"kind": "bogus"}])
        assert False, "expected ValueError"
    except ValueError:
        pass


# ==========================================================
# accumulation on chip
# ==========================================================

def test_violations_accumulate_on_chip():

    chip = make_chip()

    c = FixedMacroConstraint(macro_name="ghost", x=0, y=0)

    chip, _ = FloorplanConstraints(chip, [c]).apply()

    assert len(chip.constraint_violations) == 1
