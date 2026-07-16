from backend.floorplanning.models import (
    Chip,
    Macro,
    BlockagePlan,
    RoutingBlockage,
    PowerPlan,
    PowerStripe,
)
from backend.floorplanning.congestion_estimator import (
    CongestionEstimator,
    LAYER_STACK,
)


def make_chip(width=100, height=100, core_margin=8):
    return Chip(width=width, height=height, core_margin=core_margin)


def test_bin_grid_matches_requested_dimensions():
    chip = make_chip()
    cmap = CongestionEstimator(chip, grid_cols=5, grid_rows=4).estimate()
    assert cmap.grid_cols == 5
    assert cmap.grid_rows == 4
    assert len(cmap.bins) == 20


def test_bins_tile_the_core_exactly():
    chip = make_chip(width=100, height=100, core_margin=8)
    cmap = CongestionEstimator(chip, grid_cols=4, grid_rows=4).estimate()
    core_x0, core_y0 = chip.core_margin, chip.core_margin
    core_x1 = chip.width - chip.core_margin
    core_y1 = chip.height - chip.core_margin
    min_x = min(b.x for b in cmap.bins)
    min_y = min(b.y for b in cmap.bins)
    max_x = max(b.x + b.width for b in cmap.bins)
    max_y = max(b.y + b.height for b in cmap.bins)
    assert abs(min_x - core_x0) < 1e-6
    assert abs(min_y - core_y0) < 1e-6
    assert abs(max_x - core_x1) < 1e-6
    assert abs(max_y - core_y1) < 1e-6


def test_no_macros_no_blockages_zero_demand_full_supply():
    chip = make_chip()
    cmap = CongestionEstimator(chip, grid_cols=5, grid_rows=5).estimate()
    for b in cmap.bins:
        assert b.demand == 0.0
        assert b.congestion == 0.0
        assert not b.hotspot
        # Full stack, nothing debited -- every layer contributes
        # its full bin_area * LAYER_CAPACITY.
        assert b.supply == round(b.width * b.height * len(LAYER_STACK), 4)


def test_macro_with_cells_produces_demand_only_under_its_footprint():
    chip = make_chip(width=100, height=100, core_margin=0)
    chip.macros = [
        Macro(
            name="m0",
            macro_type="Logic",
            x=0, y=0, width=20, height=20,
            cells=[f"c{i}" for i in range(40)],
        )
    ]
    cmap = CongestionEstimator(chip, grid_cols=5, grid_rows=5, pin_density_scale=1.0).estimate()
    under_macro = [b for b in cmap.bins if b.x < 20 and b.y < 20]
    away_from_macro = [b for b in cmap.bins if b.x >= 20 or b.y >= 20]
    assert all(b.demand > 0 for b in under_macro)
    assert all(b.demand == 0 for b in away_from_macro)


def test_routing_blockage_debits_only_its_own_layer():
    chip = make_chip(width=100, height=100, core_margin=0)
    chip.blockage_plan = BlockagePlan(
        routing_blockages=[
            RoutingBlockage(layer="M1", x=0, y=0, width=100, height=100, source="macro_shadow"),
        ]
    )
    cmap = CongestionEstimator(chip, grid_cols=2, grid_rows=2).estimate()
    bin_area = cmap.bins[0].width * cmap.bins[0].height
    # M1 fully blocked, M2-M8 (7 layers) untouched.
    expected_supply = bin_area * (len(LAYER_STACK) - 1)
    for b in cmap.bins:
        assert abs(b.supply - expected_supply) < 1e-6


def test_full_stack_blockage_still_leaves_zero_supply():
    chip = make_chip(width=100, height=100, core_margin=0)
    chip.blockage_plan = BlockagePlan(
        routing_blockages=[
            RoutingBlockage(layer=layer, x=0, y=0, width=100, height=100, source="macro_shadow")
            for layer in LAYER_STACK
        ]
    )
    cmap = CongestionEstimator(chip, grid_cols=2, grid_rows=2).estimate()
    for b in cmap.bins:
        assert b.supply == 0.0


def test_macro_shadow_alone_does_not_saturate_bin_to_hotspot():
    # Regression guard: a bare macro shadow (M1-M3 only, out of
    # the full 8-layer stack) with modest cell-count demand
    # should NOT trivially read as over-capacity just because
    # 3 of 8 layers are blocked under it.
    chip = make_chip(width=100, height=100, core_margin=0)
    chip.macros = [
        Macro(
            name="m0", macro_type="Logic",
            x=0, y=0, width=100, height=100,
            cells=["c0", "c1"],
        )
    ]
    chip.blockage_plan = BlockagePlan(
        routing_blockages=[
            RoutingBlockage(layer=layer, x=0, y=0, width=100, height=100, source="macro_shadow")
            for layer in ("M1", "M2", "M3")
        ]
    )
    cmap = CongestionEstimator(chip, grid_cols=2, grid_rows=2, pin_density_scale=1.0).estimate()
    for b in cmap.bins:
        assert b.supply > 0
        assert not b.hotspot


def test_power_stripe_debits_only_its_own_layer():
    chip = make_chip(width=100, height=100, core_margin=0)
    chip.power_plan = PowerPlan(
        stripes=[PowerStripe(net="VDD", x=0, y=0, width=100, height=100, layer="M6")]
    )
    cmap = CongestionEstimator(chip, grid_cols=2, grid_rows=2).estimate()
    bin_area = cmap.bins[0].width * cmap.bins[0].height
    expected_supply = bin_area * (len(LAYER_STACK) - 1)
    for b in cmap.bins:
        assert abs(b.supply - expected_supply) < 1e-6


def test_hotspot_flagged_when_demand_exceeds_supply():
    chip = make_chip(width=100, height=100, core_margin=0)
    chip.macros = [
        Macro(
            name="m0", macro_type="Logic",
            x=0, y=0, width=100, height=100,
            cells=[f"c{i}" for i in range(1000)],
        )
    ]
    # Block the entire stack so supply is zero everywhere the
    # macro sits -- demand (>0) must then exceed supply (~0).
    chip.blockage_plan = BlockagePlan(
        routing_blockages=[
            RoutingBlockage(layer=layer, x=0, y=0, width=100, height=100, source="macro_shadow")
            for layer in LAYER_STACK
        ]
    )
    cmap = CongestionEstimator(chip, grid_cols=2, grid_rows=2, pin_density_scale=1.0).estimate()
    assert cmap.hotspots
    assert all(b.hotspot for b in cmap.bins)


def test_max_congestion_matches_worst_bin():
    chip = make_chip(width=100, height=100, core_margin=0)
    chip.macros = [
        Macro(
            name="m0", macro_type="Logic",
            x=0, y=0, width=20, height=100,
            cells=[f"c{i}" for i in range(200)],
        )
    ]
    cmap = CongestionEstimator(chip, grid_cols=5, grid_rows=1, pin_density_scale=1.0).estimate()
    assert cmap.max_congestion == max(b.congestion for b in cmap.bins)
    assert cmap.max_congestion > 0


def test_zero_grid_dims_clamped_to_at_least_one():
    chip = make_chip()
    cmap = CongestionEstimator(chip, grid_cols=0, grid_rows=0).estimate()
    assert cmap.grid_cols == 1
    assert cmap.grid_rows == 1
    assert len(cmap.bins) == 1


def test_degenerate_zero_area_core_does_not_crash():
    chip = make_chip(width=10, height=10, core_margin=5)
    cmap = CongestionEstimator(chip, grid_cols=3, grid_rows=3).estimate()
    assert len(cmap.bins) == 9
    for b in cmap.bins:
        assert b.supply == 0.0
        assert b.demand == 0.0
