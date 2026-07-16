from backend.floorplanning.models import Chip, Macro, RoutingBlockage
from backend.floorplanning.routing_blockage_manager import RoutingBlockageManager


def make_chip_with_macros(n=2):
    chip = Chip(width=100, height=100, core_margin=8)
    chip.macros = [
        Macro(name=f"m{i}", macro_type="Logic", x=i * 20, y=0, width=10, height=10)
        for i in range(n)
    ]
    return chip


def test_generates_blockage_per_macro_per_layer():

    chip = make_chip_with_macros(2)

    blockages = RoutingBlockageManager(chip, blocked_layers=("M1", "M2", "M3")).generate()

    assert len(blockages) == 6  # 2 macros * 3 layers


def test_blockage_matches_macro_footprint():

    chip = make_chip_with_macros(1)

    macro = chip.macros[0]

    blockages = RoutingBlockageManager(chip, blocked_layers=("M1",)).generate()

    b = blockages[0]

    assert b.x == macro.x
    assert b.y == macro.y
    assert b.width == macro.width
    assert b.height == macro.height
    assert b.layer == "M1"
    assert b.source == "macro_shadow"


def test_no_macros_no_blockages():

    chip = make_chip_with_macros(0)

    blockages = RoutingBlockageManager(chip).generate()

    assert blockages == []


def test_extra_blockages_appended():

    chip = make_chip_with_macros(0)

    extra = RoutingBlockage(layer="M4", x=0, y=0, width=5, height=5, source="manual")

    blockages = RoutingBlockageManager(chip).generate(extra_blockages=[extra])

    assert blockages == [extra]
