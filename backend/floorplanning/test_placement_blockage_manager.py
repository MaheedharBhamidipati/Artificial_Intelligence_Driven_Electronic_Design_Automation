from backend.floorplanning.models import Chip, Macro, PlacementBlockage
from backend.floorplanning.placement_blockage_manager import PlacementBlockageManager


def make_chip(width=100, height=100, core_margin=8, io_margin=5):
    return Chip(width=width, height=height, core_margin=core_margin, io_margin=io_margin)


def test_io_keepout_generates_four_bands():

    chip = make_chip()

    blockages = PlacementBlockageManager(chip).generate()

    assert len(blockages) == 4
    assert all(b.kind == "hard" for b in blockages)
    assert all(b.source == "io_keepout" for b in blockages)


def test_io_keepout_frames_the_die():

    chip = make_chip(width=100, height=100, io_margin=5)

    blockages = PlacementBlockageManager(chip).generate()

    # Union should touch all four die edges
    xs0 = [b.x for b in blockages]
    ys0 = [b.y for b in blockages]
    xs1 = [b.x + b.width for b in blockages]
    ys1 = [b.y + b.height for b in blockages]

    assert min(xs0) == 0
    assert min(ys0) == 0
    assert max(xs1) == 100
    assert max(ys1) == 100


def test_zero_io_margin_generates_no_keepout():

    chip = make_chip(io_margin=0)

    blockages = PlacementBlockageManager(chip).generate()

    assert blockages == []


def test_extra_blockages_included_alongside_default():

    chip = make_chip()

    extra = PlacementBlockage(kind="hard", x=40, y=40, width=5, height=5, source="manual")

    blockages = PlacementBlockageManager(chip, extra_blockages=[extra]).generate()

    assert extra in blockages
    assert len(blockages) == 5  # 4 io bands + 1 manual


def test_check_violations_flags_overlapping_macro():

    chip = make_chip()

    chip.macros = [Macro(name="m1", macro_type="Logic", x=1, y=1, width=2, height=2)]

    blockages = PlacementBlockageManager(chip).generate()

    violations = PlacementBlockageManager(chip).check_violations(blockages)

    assert len(violations) >= 1
    assert "m1" in violations[0]


def test_check_violations_clean_when_macro_inside_core():

    chip = make_chip(core_margin=8, io_margin=5)

    chip.macros = [Macro(name="m1", macro_type="Logic", x=20, y=20, width=10, height=10)]

    blockages = PlacementBlockageManager(chip).generate()

    violations = PlacementBlockageManager(chip).check_violations(blockages)

    assert violations == []


def test_soft_blockage_not_checked_as_violation():

    chip = make_chip(io_margin=0)  # no io keepout noise

    chip.macros = [Macro(name="m1", macro_type="Logic", x=1, y=1, width=2, height=2)]

    soft = PlacementBlockage(kind="soft", x=0, y=0, width=10, height=10)

    violations = PlacementBlockageManager(chip).check_violations([soft])

    assert violations == []
