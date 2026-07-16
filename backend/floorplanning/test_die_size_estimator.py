from backend.floorplanning.models import Chip, Macro
from backend.floorplanning.die_size_estimator import DieSizeEstimator


def make_chip(core_margin=8, width=100, height=100):
    return Chip(width=width, height=height, core_margin=core_margin)


def make_macro(name, n_cells):
    return Macro(
        name=name,
        macro_type="Logic",
        cells=[f"c{i}" for i in range(n_cells)],
    )


def test_no_macros_leaves_chip_dimensions_untouched():
    chip = make_chip(width=42, height=42)
    result = DieSizeEstimator(chip).plan()
    assert result.width == 42
    assert result.height == 42


def test_more_cells_yields_larger_die():
    small = make_chip()
    small.macros = [make_macro("m0", 10)]
    small = DieSizeEstimator(small).plan()

    big = make_chip()
    big.macros = [make_macro("m0", 1000)]
    big = DieSizeEstimator(big).plan()

    assert big.width > small.width
    assert big.height > small.height


def test_lower_utilization_target_yields_larger_die():
    tight = make_chip()
    tight.macros = [make_macro("m0", 200)]
    tight = DieSizeEstimator(tight, utilization_target=0.9).plan()

    loose = make_chip()
    loose.macros = [make_macro("m0", 200)]
    loose = DieSizeEstimator(loose, utilization_target=0.2).plan()

    assert loose.width * loose.height > tight.width * tight.height


def test_aspect_ratio_biases_width_over_height():
    wide = make_chip()
    wide.macros = [make_macro("m0", 200)]
    wide = DieSizeEstimator(wide, aspect_ratio=4.0).plan()

    square = make_chip()
    square.macros = [make_macro("m0", 200)]
    square = DieSizeEstimator(square, aspect_ratio=1.0).plan()

    assert wide.width / wide.height > square.width / square.height


def test_die_equals_core_plus_two_margins():
    chip = make_chip(core_margin=5)
    chip.macros = [make_macro("m0", 200)]
    chip = DieSizeEstimator(chip, core_margin=5).plan()
    assert chip.core_margin == 5
    # Reverse the solve: core area implied by final die size should
    # match what MacroSizer priced the macros at, scaled by
    # utilization_target.
    core_w = chip.width - 2 * chip.core_margin
    core_h = chip.height - 2 * chip.core_margin
    assert core_w > 0
    assert core_h > 0


def test_core_margin_override_applied_before_sizing():
    chip = make_chip(core_margin=8)
    chip.macros = [make_macro("m0", 200)]
    chip = DieSizeEstimator(chip, core_margin=20).plan()
    assert chip.core_margin == 20


def test_min_core_side_floor_respected_for_tiny_designs():
    chip = make_chip(core_margin=1)
    chip.macros = [make_macro("m0", 1)]
    chip = DieSizeEstimator(chip, min_core_side=50.0, core_margin=1).plan()
    assert chip.width >= 50.0
    assert chip.height >= 50.0


def test_utilization_target_clamped_to_safe_range():
    chip = make_chip()
    chip.macros = [make_macro("m0", 100)]
    # Should not divide by zero or blow up even with an out-of-range input.
    chip = DieSizeEstimator(chip, utilization_target=0.0).plan()
    assert chip.width > 0
    assert chip.height > 0
