from backend.floorplanning.models import (
    Chip,
    Macro,
    BlockagePlan,
    PlacementBlockage,
    ValidationReport,
    ValidationIssue,
)
from backend.floorplanning.congestion_estimator import CongestionEstimator
from backend.floorplanning.floorplan_qor_report import FloorplanQorReport


def make_chip():
    chip = Chip(width=100, height=100, core_margin=8)
    chip.macros = [Macro(name="m0", macro_type="Logic", x=10, y=10, width=10, height=10)]
    return chip


def test_generate_includes_core_metrics():
    chip = make_chip()
    report = FloorplanQorReport(chip, utilization=42.0, dead_space=58.0, estimated_wirelength=100)
    data = report.generate()
    assert data["utilization_pct"] == 42.0
    assert data["dead_space_pct"] == 58.0
    assert data["estimated_wirelength"] == 100
    assert data["macros"] == 1
    assert data["die"]["width"] == 100
    assert data["die"]["core_margin"] == 8


def test_congestion_unavailable_when_not_computed():
    chip = make_chip()
    data = FloorplanQorReport(chip, 0, 0, 0).generate()
    assert data["congestion"]["available"] is False


def test_congestion_summary_reflects_map():
    chip = make_chip()
    chip.congestion_map = CongestionEstimator(chip, grid_cols=2, grid_rows=2).estimate()
    data = FloorplanQorReport(chip, 0, 0, 0).generate()
    assert data["congestion"]["available"] is True
    assert data["congestion"]["total_bins"] == 4


def test_validation_summary_reflects_report():
    chip = make_chip()
    chip.validation_report = ValidationReport(
        issues=[
            ValidationIssue(severity="error", category="macro_overlap", message="x"),
            ValidationIssue(severity="warning", category="off_die", message="y"),
        ]
    )
    data = FloorplanQorReport(chip, 0, 0, 0).generate()
    assert data["validation"]["available"] is True
    assert data["validation"]["is_clean"] is False
    assert data["validation"]["errors"] == 1
    assert data["validation"]["warnings"] == 1


def test_blockage_summary_counts():
    chip = make_chip()
    chip.blockage_plan = BlockagePlan(
        placement_blockages=[
            PlacementBlockage(kind="hard", x=0, y=0, width=1, height=1),
            PlacementBlockage(kind="hard", x=0, y=0, width=1, height=1),
        ]
    )
    data = FloorplanQorReport(chip, 0, 0, 0).generate()
    assert data["blockages"]["placement_blockages"] == 2
    assert data["blockages"]["routing_blockages"] == 0


def test_render_text_produces_nonempty_multiline_report():
    chip = make_chip()
    text = FloorplanQorReport(chip, 42.0, 58.0, 100).render_text()
    assert "AIDEA FLOORPLAN QoR SUMMARY" in text
    assert "Utilization" in text
    assert len(text.splitlines()) > 5


def test_render_text_handles_missing_optional_stages():
    chip = Chip(width=50, height=50, core_margin=4)
    text = FloorplanQorReport(chip, 0.0, 100.0, 0).render_text()
    assert "n/a" in text
