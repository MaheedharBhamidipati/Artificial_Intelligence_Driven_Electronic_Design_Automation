from backend.floorplanning.models import Chip, Macro
from backend.floorplanning.macro_placer import MacroPlacer
from backend.floorplanning.macro_orientation_optimizer import (
    MacroOrientationOptimizer,
    UNROTATED_LABEL,
    ROTATED_LABEL,
)
from backend.floorplanning.macro_legalizer import MacroLegalizer
from backend.floorplanning.utils import overlap


def make_chip(n, cells_per_macro=8, width=100, height=100, core_margin=8):

    chip = Chip(width=width, height=height, core_margin=core_margin)

    chip.macros = [
        Macro(
            name=f"macro_{i}",
            macro_type="Logic",
            cells=[f"cell_{i}_{c}" for c in range(cells_per_macro)],
        )
        for i in range(n)
    ]

    return chip


def test_orientation_labels_are_valid():

    chip = make_chip(n=8, cells_per_macro=10)

    chip = MacroPlacer(chip, seed=3).place()

    chip = MacroOrientationOptimizer(chip, seed=3).optimize()

    for m in chip.macros:

        assert m.orientation in (UNROTATED_LABEL, ROTATED_LABEL)


def test_orientation_optimizer_explores_rotation():

    # MacroSizer gives every macro a fixed non-1.0 aspect ratio
    # (see macro_placer.MacroSizer.DEFAULT_ASPECT), so nothing
    # is square and rotation is always a real degree of freedom.
    # Across several seeds at least one run should pick a
    # rotated macro -- otherwise this "optimizer" would just be
    # an expensive no-op.
    saw_rotation = False

    for seed in range(10):

        chip = make_chip(n=10, cells_per_macro=12)

        chip = MacroPlacer(chip, seed=seed).place()

        chip = MacroOrientationOptimizer(chip, seed=seed).optimize()

        if any(m.orientation == ROTATED_LABEL for m in chip.macros):

            saw_rotation = True

            break

    assert saw_rotation, "orientation optimizer never rotated a macro across 10 seeds"


def test_rotation_swaps_dimensions_correctly():

    chip = make_chip(n=4, cells_per_macro=15)

    chip = MacroPlacer(chip, seed=5).place()

    base_dims = {m.name: (m.width, m.height) for m in chip.macros}

    chip = MacroOrientationOptimizer(chip, seed=5).optimize()

    for m in chip.macros:

        bw, bh = base_dims[m.name]

        if m.orientation == ROTATED_LABEL:

            assert abs(m.width - bh) < 1e-6
            assert abs(m.height - bw) < 1e-6

        else:

            assert abs(m.width - bw) < 1e-6
            assert abs(m.height - bh) < 1e-6


def test_full_pipeline_stays_legal_with_orientation_stage():

    for seed in range(8):

        chip = make_chip(n=9, cells_per_macro=9)

        chip = MacroPlacer(chip, seed=seed).place()

        chip = MacroOrientationOptimizer(chip, seed=seed).optimize()

        chip = MacroLegalizer(chip).legalize()

        macros = chip.macros

        for i in range(len(macros)):
            for j in range(i + 1, len(macros)):
                assert not overlap(macros[i], macros[j])

        for m in macros:

            assert m.x >= chip.core_margin - 1e-6
            assert m.y >= chip.core_margin - 1e-6
            assert m.x + m.width <= chip.width - chip.core_margin + 1e-6
            assert m.y + m.height <= chip.height - chip.core_margin + 1e-6

        std = chip.standard_cells

        for m in macros:
            assert not overlap(m, std)


def test_orientation_optimizer_no_macros():

    chip = make_chip(n=0)

    chip = MacroPlacer(chip).place()

    chip = MacroOrientationOptimizer(chip).optimize()

    assert chip.macros == []


def test_orientation_optimizer_without_prior_placement_is_a_safe_noop():

    # If MacroPlacer never ran, there's no sequence pair to
    # optimize against. Should leave macros untouched rather
    # than guessing.
    chip = make_chip(n=3)

    chip = MacroOrientationOptimizer(chip).optimize()

    for m in chip.macros:

        assert m.orientation == UNROTATED_LABEL
