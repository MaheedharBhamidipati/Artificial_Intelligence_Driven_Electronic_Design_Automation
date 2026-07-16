from backend.floorplanning.models import Chip, Macro
from backend.floorplanning.halo_keepout_generator import HaloKeepoutGenerator
from backend.floorplanning.utils import overlap_area


def make_chip():
    chip = Chip(width=100, height=100, core_margin=8)
    chip.macros = [
        Macro(name="m0", macro_type="Logic", x=20, y=20, width=10, height=10),
    ]
    return chip


def test_generates_four_bands_per_macro():
    chip = make_chip()
    blockages = HaloKeepoutGenerator(chip, halo_margin=2.0).generate()
    assert len(blockages) == 4
    assert all(b.source == "macro_halo" for b in blockages)


def test_halo_bands_do_not_overlap_the_macro_itself():
    chip = make_chip()
    macro = chip.macros[0]
    blockages = HaloKeepoutGenerator(chip, halo_margin=2.0).generate()
    # Bands are exactly adjacent to the macro (touching edges), so
    # the actual overlapping *area* must be zero -- utils.overlap()
    # itself treats touching rects as overlapping (no epsilon; see
    # macro_legalizer.py), so area is the right check here, not the
    # boolean.
    for b in blockages:
        assert overlap_area(macro, b) == 0.0


def test_halo_bands_surround_macro_footprint():
    chip = make_chip()
    macro = chip.macros[0]
    blockages = HaloKeepoutGenerator(chip, halo_margin=3.0).generate()
    min_x = min(b.x for b in blockages)
    min_y = min(b.y for b in blockages)
    max_x = max(b.x + b.width for b in blockages)
    max_y = max(b.y + b.height for b in blockages)
    assert min_x == macro.x - 3.0
    assert min_y == macro.y - 3.0
    assert max_x == macro.x + macro.width + 3.0
    assert max_y == macro.y + macro.height + 3.0


def test_zero_halo_produces_no_blockages():
    chip = make_chip()
    blockages = HaloKeepoutGenerator(chip, halo_margin=0.0).generate()
    assert blockages == []


def test_per_macro_override():
    chip = make_chip()
    chip.macros.append(
        Macro(name="m1", macro_type="Logic", x=60, y=60, width=10, height=10)
    )
    blockages = HaloKeepoutGenerator(
        chip, halo_margin=2.0, per_macro_halo={"m1": 0.0}
    ).generate()
    # m0 keeps its default halo (4 bands), m1's override zeroes it out.
    assert len(blockages) == 4


def test_kind_is_configurable():
    chip = make_chip()
    blockages = HaloKeepoutGenerator(chip, kind="soft").generate()
    assert all(b.kind == "soft" for b in blockages)


def test_no_macros_no_blockages():
    chip = Chip(width=100, height=100, core_margin=8)
    blockages = HaloKeepoutGenerator(chip).generate()
    assert blockages == []
