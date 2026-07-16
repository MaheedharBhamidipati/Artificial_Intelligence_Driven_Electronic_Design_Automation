from backend.floorplanning.models import (
    Chip,
    Macro,
    StandardCellRegion,
    PlacementBlockage,
    RoutingBlockage,
    BlockagePlan,
    PowerDomain,
    PowerDomainPlan,
    BoundaryCell,
)
from backend.floorplanning.floorplan_validator import FloorplanValidator


def make_macro(name, x, y, w=10, h=10, macro_type="Logic", domain=None):
    return Macro(name=name, macro_type=macro_type, x=x, y=y, width=w, height=h, domain=domain)


def make_chip(macros=None, width=100, height=100, core_margin=8):
    chip = Chip(width=width, height=height, core_margin=core_margin)
    chip.macros = macros or []
    return chip


# ==========================================================
# CLEAN FLOORPLAN
# ==========================================================

def test_clean_chip_produces_no_errors():

    chip = make_chip([
        make_macro("a", 10, 10),
        make_macro("b", 40, 40),
    ])

    report = FloorplanValidator(chip).validate()

    assert report.is_clean
    assert report.errors == []


def test_no_macros_is_clean():

    chip = make_chip([])

    report = FloorplanValidator(chip).validate()

    assert report.is_clean


def test_report_is_stored_on_chip():

    chip = make_chip([make_macro("a", 10, 10)])

    report = FloorplanValidator(chip).validate()

    assert chip.validation_report is report


# ==========================================================
# MACRO / MACRO OVERLAP
# ==========================================================

def test_overlapping_macros_flagged_as_error():

    chip = make_chip([
        make_macro("a", 10, 10, w=10, h=10),
        make_macro("b", 15, 15, w=10, h=10),
    ])

    report = FloorplanValidator(chip).validate()

    assert not report.is_clean
    overlaps = [i for i in report.errors if i.category == "macro_overlap"]
    assert len(overlaps) == 1
    assert "a" in overlaps[0].message and "b" in overlaps[0].message


def test_non_overlapping_macros_pass():

    chip = make_chip([
        make_macro("a", 10, 10, w=5, h=5),
        make_macro("b", 20, 20, w=5, h=5),
    ])

    report = FloorplanValidator(chip).validate()

    assert [i for i in report.issues if i.category == "macro_overlap"] == []


# ==========================================================
# OFF-DIE
# ==========================================================

def test_macro_off_die_negative_coords_flagged():

    chip = make_chip([make_macro("a", -5, 10)])

    report = FloorplanValidator(chip).validate()

    off_die = [i for i in report.errors if i.category == "off_die"]
    assert len(off_die) == 1
    assert "a" in off_die[0].message


def test_macro_off_die_past_far_edge_flagged():

    chip = make_chip([make_macro("a", 95, 95, w=10, h=10)], width=100, height=100)

    report = FloorplanValidator(chip).validate()

    off_die = [i for i in report.errors if i.category == "off_die"]
    assert len(off_die) == 1


def test_macro_fully_inside_die_not_flagged():

    chip = make_chip([make_macro("a", 0, 0, w=10, h=10)], width=100, height=100)

    report = FloorplanValidator(chip).validate()

    assert [i for i in report.issues if i.category == "off_die"] == []


# ==========================================================
# STANDARD CELL REGION OVERLAP
# ==========================================================

def test_macro_overlapping_standard_cell_region_flagged():

    chip = make_chip([make_macro("a", 10, 10, w=10, h=10)])
    chip.standard_cells = StandardCellRegion(x=5, y=5, width=20, height=20)

    report = FloorplanValidator(chip).validate()

    sc_issues = [i for i in report.errors if i.category == "standard_cell_overlap"]
    assert len(sc_issues) == 1


def test_macro_clear_of_standard_cell_region_passes():

    chip = make_chip([make_macro("a", 50, 50, w=10, h=10)])
    chip.standard_cells = StandardCellRegion(x=0, y=0, width=20, height=20)

    report = FloorplanValidator(chip).validate()

    assert [i for i in report.issues if i.category == "standard_cell_overlap"] == []


def test_no_standard_cell_region_never_flags():

    chip = make_chip([make_macro("a", 10, 10)])
    chip.standard_cells = None

    report = FloorplanValidator(chip).validate()

    assert [i for i in report.issues if i.category == "standard_cell_overlap"] == []


# ==========================================================
# HARD BLOCKAGES
# ==========================================================

def test_macro_overlapping_hard_blockage_flagged():

    chip = make_chip([make_macro("a", 1, 1, w=4, h=4)])
    chip.blockage_plan = BlockagePlan(
        placement_blockages=[
            PlacementBlockage(kind="hard", x=0, y=0, width=5, height=5, source="io_keepout"),
        ],
        routing_blockages=[],
    )

    report = FloorplanValidator(chip).validate()

    blockage_issues = [i for i in report.errors if i.category == "blockage"]
    assert len(blockage_issues) == 1
    assert "io_keepout" in blockage_issues[0].message


def test_macro_overlapping_soft_blockage_not_flagged():

    chip = make_chip([make_macro("a", 1, 1, w=4, h=4)])
    chip.blockage_plan = BlockagePlan(
        placement_blockages=[
            PlacementBlockage(kind="soft", x=0, y=0, width=5, height=5),
        ],
        routing_blockages=[],
    )

    report = FloorplanValidator(chip).validate()

    assert [i for i in report.issues if i.category == "blockage"] == []


def test_no_blockage_plan_never_flags():

    chip = make_chip([make_macro("a", 10, 10)])
    chip.blockage_plan = None

    report = FloorplanValidator(chip).validate()

    assert [i for i in report.issues if i.category == "blockage"] == []


def test_routing_blockages_are_not_checked_for_placement_overlap():

    # Routing blockages are a router's concern, not placement
    # legality -- a macro sitting inside its own macro-shadow
    # routing blockage is completely normal and must not flag.
    chip = make_chip([make_macro("a", 10, 10, w=10, h=10)])
    chip.blockage_plan = BlockagePlan(
        placement_blockages=[],
        routing_blockages=[
            RoutingBlockage(layer="M1", x=10, y=10, width=10, height=10, source="macro_shadow"),
        ],
    )

    report = FloorplanValidator(chip).validate()

    assert report.is_clean


# ==========================================================
# CONSTRAINT VIOLATIONS ROLLUP
# ==========================================================

def test_constraint_violations_rolled_into_report():

    chip = make_chip([make_macro("a", 10, 10)])
    chip.constraint_violations = ["fixed_macro 'x' references unknown macro"]

    report = FloorplanValidator(chip).validate()

    constraint_issues = [i for i in report.errors if i.category == "constraint"]
    assert len(constraint_issues) == 1
    assert constraint_issues[0].message == "fixed_macro 'x' references unknown macro"


def test_no_constraint_violations_means_no_constraint_issues():

    chip = make_chip([make_macro("a", 10, 10)])

    report = FloorplanValidator(chip).validate()

    assert [i for i in report.issues if i.category == "constraint"] == []


# ==========================================================
# POWER DOMAIN SANITY
# ==========================================================

def test_macro_domain_not_in_plan_flagged():

    chip = make_chip([make_macro("a", 10, 10, domain="PD_9.99V")])
    chip.power_domain_plan = PowerDomainPlan(domains=[], boundary_cells=[])

    report = FloorplanValidator(chip).validate()

    domain_issues = [i for i in report.errors if i.category == "power_domain"]
    assert len(domain_issues) == 1
    assert "PD_9.99V" in domain_issues[0].message


def test_macro_domain_matching_plan_entry_passes():

    chip = make_chip([make_macro("a", 10, 10, w=10, h=10, domain="PD_0.80V")])
    chip.power_domain_plan = PowerDomainPlan(
        domains=[
            PowerDomain(name="PD_0.80V", voltage=0.8, x=10, y=10, width=10, height=10, macros=["a"]),
        ],
        boundary_cells=[],
    )

    report = FloorplanValidator(chip).validate()

    assert [i for i in report.issues if i.category == "power_domain"] == []


def test_boundary_cell_unknown_domain_flagged():

    chip = make_chip([make_macro("a", 10, 10)])
    chip.power_domain_plan = PowerDomainPlan(
        domains=[
            PowerDomain(name="PD_0.80V", voltage=0.8, x=0, y=0, width=10, height=10, macros=[]),
        ],
        boundary_cells=[
            BoundaryCell(kind="isolation", x=5, y=5, from_domain="PD_0.80V", to_domain="PD_9.99V"),
        ],
    )

    report = FloorplanValidator(chip).validate()

    domain_issues = [i for i in report.errors if i.category == "power_domain"]
    assert len(domain_issues) == 1
    assert "PD_9.99V" in domain_issues[0].message


def test_macro_moved_outside_domain_bbox_is_a_warning_not_error():

    # Domain box was computed when 'a' sat at (10, 10); a later
    # FixedMacroConstraint moved it to (90, 90) without anyone
    # recomputing the domain's bounding box.
    chip = make_chip([make_macro("a", 90, 90, w=5, h=5, domain="PD_0.80V")])
    chip.power_domain_plan = PowerDomainPlan(
        domains=[
            PowerDomain(name="PD_0.80V", voltage=0.8, x=10, y=10, width=10, height=10, macros=["a"]),
        ],
        boundary_cells=[],
    )

    report = FloorplanValidator(chip).validate()

    assert report.is_clean  # warning only, not an error
    warnings = [i for i in report.warnings if i.category == "power_domain"]
    assert len(warnings) == 1
    assert "a" in warnings[0].message


def test_domain_referencing_unknown_macro_flagged():

    chip = make_chip([])
    chip.power_domain_plan = PowerDomainPlan(
        domains=[
            PowerDomain(name="PD_0.80V", voltage=0.8, x=0, y=0, width=10, height=10, macros=["ghost"]),
        ],
        boundary_cells=[],
    )

    report = FloorplanValidator(chip).validate()

    domain_issues = [i for i in report.errors if i.category == "power_domain"]
    assert len(domain_issues) == 1
    assert "ghost" in domain_issues[0].message


def test_no_power_domain_plan_never_flags():

    chip = make_chip([make_macro("a", 10, 10, domain="whatever")])
    chip.power_domain_plan = None

    report = FloorplanValidator(chip).validate()

    assert [i for i in report.issues if i.category == "power_domain"] == []


def test_macro_with_no_domain_never_flagged():

    chip = make_chip([make_macro("a", 10, 10, domain=None)])
    chip.power_domain_plan = PowerDomainPlan(domains=[], boundary_cells=[])

    report = FloorplanValidator(chip).validate()

    assert [i for i in report.issues if i.category == "power_domain"] == []


# ==========================================================
# MULTIPLE ISSUE CATEGORIES TOGETHER
# ==========================================================

def test_multiple_categories_all_reported_together():

    chip = make_chip([
        make_macro("a", 10, 10, w=10, h=10),
        make_macro("b", 15, 15, w=10, h=10),   # overlaps a
        make_macro("c", 95, 95, w=10, h=10),   # off-die
    ])
    chip.constraint_violations = ["some prior violation"]

    report = FloorplanValidator(chip).validate()

    categories = {i.category for i in report.issues}
    assert "macro_overlap" in categories
    assert "off_die" in categories
    assert "constraint" in categories
    assert not report.is_clean
