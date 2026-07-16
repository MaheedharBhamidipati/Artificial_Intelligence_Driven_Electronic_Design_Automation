from backend.floorplanning.models import Chip, Macro
from backend.floorplanning.macro_placer import (
    MacroPlacer,
    MacroSizer,
    decode_sequence_pair,
)
from backend.floorplanning.macro_legalizer import MacroLegalizer
from backend.floorplanning.utils import overlap


def make_chip(n, cells_per_macro=5, width=100, height=100, core_margin=8):

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


# ==========================================================
# SEQUENCE PAIR DECODE: no overlaps by construction
# ==========================================================

def test_decode_sequence_pair_no_overlap():

    widths = [10, 8, 6, 12, 5]

    heights = [6, 9, 4, 5, 7]

    seq_plus = [0, 1, 2, 3, 4]

    seq_minus = [4, 1, 0, 3, 2]

    x, y, bbox_w, bbox_h = decode_sequence_pair(
        seq_plus, seq_minus, widths, heights, spacing=1.0
    )

    class R:
        def __init__(self, x, y, w, h):
            self.x, self.y, self.width, self.height = x, y, w, h

    rects = [
        R(x[i], y[i], widths[i], heights[i]) for i in range(len(widths))
    ]

    for i in range(len(rects)):
        for j in range(i + 1, len(rects)):
            assert not overlap(rects[i], rects[j])

    assert bbox_w >= max(x[i] + widths[i] for i in range(len(widths)))
    assert bbox_h >= max(y[i] + heights[i] for i in range(len(widths)))


# ==========================================================
# MACRO SIZER: bigger macros get bigger footprints
# ==========================================================

def test_macro_sizer_scales_with_cell_count():

    small = Macro(name="s", macro_type="Logic", cells=["a"])

    big = Macro(name="b", macro_type="Logic", cells=[f"c{i}" for i in range(50)])

    MacroSizer().size([small, big])

    assert big.width * big.height > small.width * small.height


# ==========================================================
# MACRO PLACER + LEGALIZER: end-to-end, no overlaps, in bounds
# ==========================================================

def test_placer_and_legalizer_no_overlap_and_in_bounds():

    chip = make_chip(n=6, cells_per_macro=8)

    chip = MacroPlacer(chip, seed=42).place()

    chip = MacroLegalizer(chip).legalize()

    macros = chip.macros

    for i in range(len(macros)):
        for j in range(i + 1, len(macros)):
            assert not overlap(macros[i], macros[j]), (
                f"{macros[i].name} overlaps {macros[j].name}"
            )

    for m in macros:

        assert m.x >= chip.core_margin - 1e-6

        assert m.y >= chip.core_margin - 1e-6

        assert m.x + m.width <= chip.width - chip.core_margin + 1e-6

        assert m.y + m.height <= chip.height - chip.core_margin + 1e-6

    assert chip.standard_cells is not None

    assert chip.standard_cells.height > 0

    std = chip.standard_cells

    for m in macros:

        assert not overlap(m, std), (
            f"{m.name} overlaps the standard-cell region"
        )


def test_placer_handles_single_macro():

    chip = make_chip(n=1)

    chip = MacroPlacer(chip, seed=1).place()

    chip = MacroLegalizer(chip).legalize()

    m = chip.macros[0]

    assert m.width > 0 and m.height > 0

    assert m.x >= chip.core_margin - 1e-6

    assert m.y >= chip.core_margin - 1e-6


def test_placer_handles_no_macros():

    chip = make_chip(n=0)

    chip = MacroPlacer(chip).place()

    chip = MacroLegalizer(chip).legalize()

    assert chip.macros == []

    assert chip.standard_cells is not None


def test_placer_is_reproducible_with_seed():

    chip_a = make_chip(n=5, cells_per_macro=6)

    chip_b = make_chip(n=5, cells_per_macro=6)

    MacroPlacer(chip_a, seed=7).place()

    MacroPlacer(chip_b, seed=7).place()

    for ma, mb in zip(chip_a.macros, chip_b.macros):

        assert ma.x == mb.x
        assert ma.y == mb.y
