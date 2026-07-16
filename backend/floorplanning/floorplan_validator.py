"""
=========================================================
AIDEA FLOORPLANNER

Floorplan Validator

DRC-style validation pass that runs last, after every other
stage (placement, legalization, constraints, blockages,
power domains) has finished touching the chip. It doesn't
generate or fix anything -- everything it flags was already
possible to introduce upstream (a FixedMacroConstraint can
reintroduce overlap; grid-snap rounding can in theory still
leave a residual overlap MacroLegalizer's own sweep missed;
a constraint can push a macro off-die or into the
standard-cell band) -- this file is the single place that
re-checks the *finished* chip end to end and rolls every
category of problem into one report, the same way a real
DRC deck runs after route rather than trusting each upstream
tool got everything right.

Categories checked:

    1. macro_overlap          -- pairwise macro/macro overlap,
                                  via utils.overlap()
    2. off_die                -- any macro (even partially)
                                  outside [0, width] x [0, height]
    3. standard_cell_overlap  -- any macro overlapping the
                                  standard-cell region MacroLegalizer
                                  placed
    4. blockage               -- any macro overlapping a "hard"
                                  entry in chip.blockage_plan
                                  (io keepout + manual/constraint-
                                  derived blockages alike);
                                  independent of whatever
                                  PlacementBlockageManager.check_
                                  violations() already ran during
                                  generate(), since a constraint can
                                  move a macro *after* that check ran
    5. constraint              -- rolled up from
                                  chip.constraint_violations (not
                                  re-derived -- FloorplanConstraints
                                  already owns that logic, this just
                                  folds its output into one report)
    6. power_domain            -- macro.domain / boundary-cell
                                  domain references that don't
                                  resolve to an entry in
                                  chip.power_domain_plan.domains,
                                  plus a soft check that each
                                  domain's stored bounding box still
                                  covers its member macros

Everything above is an "error" (the floorplan is not legal)
except the power-domain bounding-box drift check, which is a
"warning": a domain box going stale after a later constraint
move doesn't make the floorplan illegal by itself, it just
means PowerDomainManager's numbers are no longer accurate.
=========================================================
"""

from backend.floorplanning.models import ValidationIssue, ValidationReport
from backend.floorplanning.utils import overlap


class FloorplanValidator:

    def __init__(self, chip):

        self.chip = chip

    # ------------------------------------------------------

    @staticmethod
    def _error(category, message):

        return ValidationIssue(severity="error", category=category, message=message)

    @staticmethod
    def _warning(category, message):

        return ValidationIssue(severity="warning", category=category, message=message)

    # ------------------------------------------------------
    # 1. MACRO / MACRO OVERLAP
    # ------------------------------------------------------

    def _check_macro_overlaps(self):

        issues = []

        macros = self.chip.macros

        for i in range(len(macros)):

            for j in range(i + 1, len(macros)):

                a, b = macros[i], macros[j]

                if overlap(a, b):

                    issues.append(
                        self._error(
                            "macro_overlap",
                            f"macro '{a.name}' overlaps macro '{b.name}'",
                        )
                    )

        return issues

    # ------------------------------------------------------
    # 2. OFF-DIE PLACEMENT
    # ------------------------------------------------------

    def _check_off_die(self):

        issues = []

        chip = self.chip

        for macro in chip.macros:

            off_die = (
                macro.x < 0
                or macro.y < 0
                or macro.x + macro.width > chip.width
                or macro.y + macro.height > chip.height
            )

            if off_die:

                issues.append(
                    self._error(
                        "off_die",
                        f"macro '{macro.name}' at "
                        f"({macro.x}, {macro.y}, {macro.width}x{macro.height}) "
                        f"falls outside the die ({chip.width}x{chip.height})",
                    )
                )

        return issues

    # ------------------------------------------------------
    # 3. STANDARD-CELL REGION OVERLAP
    # ------------------------------------------------------

    def _check_standard_cell_overlap(self):

        issues = []

        chip = self.chip

        if chip.standard_cells is None:
            return issues

        for macro in chip.macros:

            if overlap(macro, chip.standard_cells):

                region = chip.standard_cells

                issues.append(
                    self._error(
                        "standard_cell_overlap",
                        f"macro '{macro.name}' overlaps the standard-cell "
                        f"region ({region.x}, {region.y}, "
                        f"{region.width}x{region.height})",
                    )
                )

        return issues

    # ------------------------------------------------------
    # 4. HARD PLACEMENT BLOCKAGES
    # ------------------------------------------------------

    def _check_hard_blockages(self):

        issues = []

        chip = self.chip

        if chip.blockage_plan is None:
            return issues

        hard_blockages = [
            b for b in chip.blockage_plan.placement_blockages if b.kind == "hard"
        ]

        for macro in chip.macros:

            for blockage in hard_blockages:

                if overlap(macro, blockage):

                    issues.append(
                        self._error(
                            "blockage",
                            f"macro '{macro.name}' overlaps hard placement "
                            f"blockage ({blockage.source}) at "
                            f"({blockage.x}, {blockage.y}, "
                            f"{blockage.width}x{blockage.height})",
                        )
                    )

        return issues

    # ------------------------------------------------------
    # 5. CONSTRAINT VIOLATIONS ROLLUP
    # ------------------------------------------------------

    def _check_constraint_violations(self):

        return [
            self._error("constraint", message)
            for message in self.chip.constraint_violations
        ]

    # ------------------------------------------------------
    # 6. POWER DOMAIN SANITY
    # ------------------------------------------------------

    def _check_power_domains(self):

        issues = []

        chip = self.chip

        if chip.power_domain_plan is None:
            return issues

        domain_names = {d.name for d in chip.power_domain_plan.domains}

        for macro in chip.macros:

            if macro.domain is not None and macro.domain not in domain_names:

                issues.append(
                    self._error(
                        "power_domain",
                        f"macro '{macro.name}' is assigned to domain "
                        f"'{macro.domain}', which has no matching entry "
                        f"in chip.power_domain_plan.domains",
                    )
                )

        for cell in chip.power_domain_plan.boundary_cells:

            for domain_name in (cell.from_domain, cell.to_domain):

                if domain_name not in domain_names:

                    issues.append(
                        self._error(
                            "power_domain",
                            f"boundary cell ({cell.kind}) references "
                            f"unknown domain '{domain_name}'",
                        )
                    )

        macros_by_name = {m.name: m for m in chip.macros}

        for domain in chip.power_domain_plan.domains:

            dx0, dy0 = domain.x, domain.y

            dx1, dy1 = domain.x + domain.width, domain.y + domain.height

            for macro_name in domain.macros:

                macro = macros_by_name.get(macro_name)

                if macro is None:

                    issues.append(
                        self._error(
                            "power_domain",
                            f"domain '{domain.name}' references unknown "
                            f"macro '{macro_name}'",
                        )
                    )

                    continue

                inside = (
                    macro.x >= dx0
                    and macro.y >= dy0
                    and macro.x + macro.width <= dx1
                    and macro.y + macro.height <= dy1
                )

                if not inside:

                    issues.append(
                        self._warning(
                            "power_domain",
                            f"macro '{macro.name}' has moved outside the "
                            f"stored bounding box of its domain "
                            f"'{domain.name}'",
                        )
                    )

        return issues

    # ------------------------------------------------------

    def validate(self):

        issues = []

        issues.extend(self._check_macro_overlaps())

        issues.extend(self._check_off_die())

        issues.extend(self._check_standard_cell_overlap())

        issues.extend(self._check_hard_blockages())

        issues.extend(self._check_power_domains())

        issues.extend(self._check_constraint_violations())

        report = ValidationReport(issues=issues)

        self.chip.validation_report = report

        return report
