"""
=========================================================
AIDEA FLOORPLANNER

Floorplan QoR Report

Pulls together everything FloorplanEngine's stages already
computed -- utilization, dead space, wirelength estimate,
congestion, validation, blockages, power planning -- into one
Innovus/ICC2-style QoR summary. Read-only and computes nothing
new about the design: every number here already exists
somewhere on Chip/FloorplanResult, this file just reassembles
it into the shape a caller (or a report file) actually wants,
instead of leaving that assembly to every caller separately.
=========================================================
"""


class FloorplanQorReport:

    def __init__(self, chip, utilization, dead_space, estimated_wirelength):

        self.chip = chip

        self.utilization = utilization

        self.dead_space = dead_space

        self.estimated_wirelength = estimated_wirelength

    # ------------------------------------------------------

    def _congestion_summary(self):

        cmap = getattr(self.chip, "congestion_map", None)

        if cmap is None:
            return {"available": False}

        return {
            "available": True,
            "max_congestion": cmap.max_congestion,
            "hotspot_bins": len(cmap.hotspots),
            "total_bins": len(cmap.bins),
        }

    # ------------------------------------------------------

    def _validation_summary(self):

        report = getattr(self.chip, "validation_report", None)

        if report is None:
            return {"available": False}

        return {
            "available": True,
            "is_clean": report.is_clean,
            "errors": len(report.errors),
            "warnings": len(report.warnings),
        }

    # ------------------------------------------------------

    def _blockage_summary(self):

        plan = getattr(self.chip, "blockage_plan", None)

        if plan is None:
            return {"placement_blockages": 0, "routing_blockages": 0}

        return {
            "placement_blockages": len(plan.placement_blockages),
            "routing_blockages": len(plan.routing_blockages),
        }

    # ------------------------------------------------------

    def _power_summary(self):

        domain_plan = getattr(self.chip, "power_domain_plan", None)

        power_plan = getattr(self.chip, "power_plan", None)

        return {
            "domains": len(domain_plan.domains) if domain_plan else 0,
            "boundary_cells": len(domain_plan.boundary_cells) if domain_plan else 0,
            "rings": len(power_plan.rings) if power_plan else 0,
            "stripes": len(power_plan.stripes) if power_plan else 0,
            "vias": len(power_plan.vias) if power_plan else 0,
        }

    # ------------------------------------------------------

    def generate(self):

        chip = self.chip

        return {
            "die": {
                "width": chip.width,
                "height": chip.height,
                "core_margin": chip.core_margin,
            },
            "macros": len(chip.macros),
            "utilization_pct": self.utilization,
            "dead_space_pct": self.dead_space,
            "estimated_wirelength": self.estimated_wirelength,
            "congestion": self._congestion_summary(),
            "validation": self._validation_summary(),
            "blockages": self._blockage_summary(),
            "power": self._power_summary(),
            "constraint_violations": len(chip.constraint_violations),
        }

    # ------------------------------------------------------

    def render_text(self):

        data = self.generate()

        lines = []

        lines.append("=" * 56)
        lines.append("AIDEA FLOORPLAN QoR SUMMARY")
        lines.append("=" * 56)

        die = data["die"]
        lines.append(
            f"Die            : {die['width']} x {die['height']} "
            f"(core margin {die['core_margin']})"
        )

        lines.append(f"Macros         : {data['macros']}")
        lines.append(f"Utilization    : {data['utilization_pct']}%")
        lines.append(f"Dead space     : {data['dead_space_pct']}%")
        lines.append(f"Est. wirelength: {data['estimated_wirelength']}")

        cong = data["congestion"]

        if cong["available"]:
            lines.append(
                f"Congestion     : max {cong['max_congestion']}, "
                f"hotspots {cong['hotspot_bins']}/{cong['total_bins']} bins"
            )
        else:
            lines.append("Congestion     : n/a")

        val = data["validation"]

        if val["available"]:
            status = "CLEAN" if val["is_clean"] else "ISSUES FOUND"
            lines.append(
                f"Validation     : {status} "
                f"({val['errors']} errors, {val['warnings']} warnings)"
            )
        else:
            lines.append("Validation     : n/a")

        blk = data["blockages"]
        lines.append(
            f"Blockages      : {blk['placement_blockages']} placement, "
            f"{blk['routing_blockages']} routing"
        )

        pwr = data["power"]
        lines.append(
            f"Power domains  : {pwr['domains']} "
            f"(boundary cells {pwr['boundary_cells']})"
        )
        lines.append(
            f"PDN            : {pwr['rings']} rings, "
            f"{pwr['stripes']} stripes, {pwr['vias']} vias"
        )

        lines.append(f"Constraint violations: {data['constraint_violations']}")
        lines.append("=" * 56)

        return "\n".join(lines)
