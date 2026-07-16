"""
=========================================================
AIDEA FLOORPLANNER

Floorplan Constraints

A deliberately small, structured stand-in for what a real
flow pulls from an SDC / floorplan-constraints file at this
stage: pin a macro's exact coordinates, confine a set of
macros to a named region, and loosely group macros that
should end up near each other. Not an SDC grammar parser --
from_dicts() builds the three constraint types in models.py
from plain dicts, which is the realistic integration point
(a caller upstream owns actual SDC/UPF parsing and hands
this file structured data).

Runs LAST in the pipeline (after legalization), for the
same reason DEF ends with fixed-placement overrides: a
FixedMacroConstraint is allowed to override wherever the
optimizer/legalizer decided to put a macro. That means a
fixed macro can reintroduce overlap with a macro the
annealer never got the chance to route around -- this file
does not try to resolve that (nothing this small should
silently rewrite a real constraint), it just reports it via
apply()'s returned violations list, the same as
PlacementBlockageManager does for blockages.
=========================================================
"""

from backend.floorplanning.models import (
    FixedMacroConstraint,
    RegionConstraint,
    GroupGuideConstraint,
)
from backend.floorplanning.utils import overlap


class FloorplanConstraints:

    def __init__(self, chip, constraints=None):

        self.chip = chip

        self.constraints = list(constraints or [])

    # ------------------------------------------------------
    # BUILD FROM PLAIN DICTS
    # ------------------------------------------------------

    @staticmethod
    def from_dicts(specs):

        constraints = []

        for spec in specs:

            kind = spec.get("kind")

            if kind == "fixed_macro":

                constraints.append(
                    FixedMacroConstraint(
                        macro_name=spec["macro_name"],
                        x=spec["x"],
                        y=spec["y"],
                    )
                )

            elif kind == "region":

                constraints.append(
                    RegionConstraint(
                        name=spec["name"],
                        x=spec["x"],
                        y=spec["y"],
                        width=spec["width"],
                        height=spec["height"],
                        macro_names=spec.get("macro_names", []),
                    )
                )

            elif kind == "group_guide":

                constraints.append(
                    GroupGuideConstraint(
                        name=spec["name"],
                        macro_names=spec.get("macro_names", []),
                        max_span=spec.get("max_span"),
                    )
                )

            else:

                raise ValueError(f"Unknown constraint kind: {kind!r}")

        return constraints

    # ------------------------------------------------------

    def _macros_by_name(self):

        return {m.name: m for m in self.chip.macros}

    # ------------------------------------------------------
    # FIXED MACRO
    # ------------------------------------------------------

    def _apply_fixed_macro(self, constraint, macros_by_name, violations):

        macro = macros_by_name.get(constraint.macro_name)

        if macro is None:

            violations.append(
                f"fixed_macro constraint references unknown macro "
                f"'{constraint.macro_name}'"
            )

            return

        macro.x = constraint.x

        macro.y = constraint.y

        macro.fixed = True

        # A moved macro can now legitimately overlap whatever the
        # annealer/legalizer placed nearby -- report it rather than
        # silently leaving a bad floorplan.
        for other in self.chip.macros:

            if other is macro:
                continue

            if overlap(macro, other):

                violations.append(
                    f"fixed_macro '{macro.name}' at "
                    f"({constraint.x}, {constraint.y}) now overlaps "
                    f"'{other.name}'"
                )

    # ------------------------------------------------------
    # REGION
    # ------------------------------------------------------

    def _apply_region(self, constraint, macros_by_name, violations):

        rx0, ry0 = constraint.x, constraint.y

        rx1, ry1 = constraint.x + constraint.width, constraint.y + constraint.height

        for name in constraint.macro_names:

            macro = macros_by_name.get(name)

            if macro is None:

                violations.append(
                    f"region constraint '{constraint.name}' references "
                    f"unknown macro '{name}'"
                )

                continue

            inside = (
                macro.x >= rx0
                and macro.y >= ry0
                and macro.x + macro.width <= rx1
                and macro.y + macro.height <= ry1
            )

            if not inside:

                violations.append(
                    f"macro '{name}' violates region constraint "
                    f"'{constraint.name}' "
                    f"({rx0}, {ry0}, {constraint.width}x{constraint.height})"
                )

    # ------------------------------------------------------
    # GROUP GUIDE
    # ------------------------------------------------------

    def _apply_group_guide(self, constraint, macros_by_name, violations):

        members = [macros_by_name.get(n) for n in constraint.macro_names]

        members = [m for m in members if m is not None]

        missing = set(constraint.macro_names) - {m.name for m in members}

        for name in missing:

            violations.append(
                f"group_guide constraint '{constraint.name}' references "
                f"unknown macro '{name}'"
            )

        if constraint.max_span is None or len(members) < 2:
            return

        xs0 = [m.x for m in members]

        ys0 = [m.y for m in members]

        xs1 = [m.x + m.width for m in members]

        ys1 = [m.y + m.height for m in members]

        span = max(max(xs1) - min(xs0), max(ys1) - min(ys0))

        if span > constraint.max_span:

            violations.append(
                f"group_guide '{constraint.name}' span {round(span, 2)} "
                f"exceeds max_span {constraint.max_span}"
            )

    # ------------------------------------------------------

    def apply(self):

        macros_by_name = self._macros_by_name()

        violations = []

        for constraint in self.constraints:

            if isinstance(constraint, FixedMacroConstraint):

                self._apply_fixed_macro(constraint, macros_by_name, violations)

            elif isinstance(constraint, RegionConstraint):

                self._apply_region(constraint, macros_by_name, violations)

            elif isinstance(constraint, GroupGuideConstraint):

                self._apply_group_guide(constraint, macros_by_name, violations)

            else:

                violations.append(f"Unknown constraint object: {constraint!r}")

        self.chip.constraint_violations.extend(violations)

        return self.chip, violations
