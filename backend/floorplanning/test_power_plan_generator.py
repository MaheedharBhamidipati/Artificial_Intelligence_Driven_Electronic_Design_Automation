from backend.floorplanning.models import Chip
from backend.floorplanning.power_ring_generator import PowerRingGenerator
from backend.floorplanning.power_stripe_generator import PowerStripeGenerator
from backend.floorplanning.pg_via_generator import PGViaGenerator
from backend.floorplanning.power_plan_generator import PowerPlanGenerator


def make_chip(width=100, height=100, core_margin=8):
    return Chip(width=width, height=height, core_margin=core_margin)


def test_two_rings_generated_and_nested():
    chip = make_chip()
    rings = PowerRingGenerator(chip).generate()
    assert len(rings) == 2
    vdd, vss = rings[0], rings[1]
    assert vdd.net == "VDD"
    assert vss.net == "VSS"
    assert vss.x > vdd.x
    assert vss.y > vdd.y
    assert vss.x + vss.width < vdd.x + vdd.width
    assert vss.y + vss.height < vdd.y + vdd.height


def test_rings_stay_within_core_bounds():
    chip = make_chip()
    rings = PowerRingGenerator(chip).generate()
    core_x0, core_y0 = chip.core_margin, chip.core_margin
    core_x1 = chip.width - chip.core_margin
    core_y1 = chip.height - chip.core_margin
    for ring in rings:
        assert ring.x >= core_x0 - 1e-6
        assert ring.y >= core_y0 - 1e-6
        assert ring.x + ring.width <= core_x1 + 1e-6
        assert ring.y + ring.height <= core_y1 + 1e-6


def test_ring_generation_degrades_gracefully_on_tiny_core():
    chip = make_chip(width=10, height=10, core_margin=4)
    rings = PowerRingGenerator(chip, ring_width=5, ring_spacing=5).generate()
    for ring in rings:
        assert ring.width > 0
        assert ring.height > 0


def test_each_net_stripes_reach_its_own_ring():
    chip = make_chip()
    rings = PowerRingGenerator(chip).generate()
    ring_by_net = {r.net: r for r in rings}
    stripes = PowerStripeGenerator(chip, rings, pitch=15.0).generate()
    assert stripes
    for stripe in stripes:
        ring = ring_by_net[stripe.net]
        if stripe.is_vertical:
            assert abs(stripe.y - ring.y) < 1e-6
            assert abs((stripe.y + stripe.height) - (ring.y + ring.height)) < 1e-6
        else:
            assert abs(stripe.x - ring.x) < 1e-6
            assert abs((stripe.x + stripe.width) - (ring.x + ring.width)) < 1e-6


def test_vdd_and_vss_stripes_have_different_reach():
    chip = make_chip()
    rings = PowerRingGenerator(chip).generate()
    stripes = PowerStripeGenerator(chip, rings, pitch=12.0).generate()
    vdd_vertical = [s for s in stripes if s.net == "VDD" and s.is_vertical]
    vss_vertical = [s for s in stripes if s.net == "VSS" and s.is_vertical]
    assert vdd_vertical and vss_vertical
    assert vdd_vertical[0].height > vss_vertical[0].height


def test_no_stripes_when_no_rings():
    chip = make_chip()
    stripes = PowerStripeGenerator(chip, [], pitch=10.0).generate()
    assert stripes == []


def test_vias_generated_between_stripes_and_rings():
    chip = make_chip()
    rings = PowerRingGenerator(chip).generate()
    stripes = PowerStripeGenerator(chip, rings, pitch=15.0).generate()
    vias = PGViaGenerator(chip, rings, stripes).generate()
    assert vias
    nets_present = {r.net for r in rings}
    for via in vias:
        assert via.net in nets_present


def test_no_cross_net_vias():
    chip = make_chip()
    rings = PowerRingGenerator(chip).generate()
    stripes = PowerStripeGenerator(chip, rings, pitch=15.0).generate()
    vias = PGViaGenerator(chip, rings, stripes).generate()
    ring_by_net = {r.net: r for r in rings}
    for via in vias:
        ring = ring_by_net[via.net]
        if via.layer_to != ring.layer:
            continue
        ox0, oy0 = ring.x, ring.y
        ox1, oy1 = ring.x + ring.width, ring.y + ring.height
        assert ox0 - 1e-6 <= via.x <= ox1 + 1e-6
        assert oy0 - 1e-6 <= via.y <= oy1 + 1e-6


def test_stripe_stripe_vias_only_between_orthogonal_same_net():
    chip = make_chip()
    rings = PowerRingGenerator(chip).generate()
    stripes = PowerStripeGenerator(chip, rings, pitch=15.0).generate()
    gen = PGViaGenerator(chip, rings, stripes)
    stripe_stripe_vias = gen._stripe_stripe_vias()
    for via in stripe_stripe_vias:
        assert via.layer_from == "M6"
        assert via.layer_to == "M6"


def test_power_plan_generator_populates_chip():
    chip = make_chip()
    chip = PowerPlanGenerator(chip).generate()
    assert chip.power_plan is not None
    assert len(chip.power_plan.rings) == 2
    assert len(chip.power_plan.stripes) > 0
    assert len(chip.power_plan.vias) > 0


def test_power_plan_generator_deterministic():
    chip_a = PowerPlanGenerator(make_chip()).generate()
    chip_b = PowerPlanGenerator(make_chip()).generate()
    assert len(chip_a.power_plan.stripes) == len(chip_b.power_plan.stripes)
    assert len(chip_a.power_plan.vias) == len(chip_b.power_plan.vias)


def test_power_plan_generator_handles_small_die_without_crash():
    chip = make_chip(width=20, height=20, core_margin=2)
    chip = PowerPlanGenerator(
        chip, ring_width=1.0, ring_spacing=0.5, stripe_pitch=3.0,
    ).generate()
    assert chip.power_plan is not None
