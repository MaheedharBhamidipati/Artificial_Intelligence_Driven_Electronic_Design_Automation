"""
=========================================================
AIDEA FLOORPLANNER

Netlist Connectivity

Wires the real netlist graph -- Module.nets (Yosys bit-id
groups) and Cell.connections (per-cell port -> bit-id map) --
through to macro-level connectivity, which is the piece
MacroBuilder deliberately does not do (it groups cells by
category only, see macro_builder.py).

This module does not change how macros are built or placed.
It is a read-only derivation that runs *after* MacroBuilder:
given the macros MacroBuilder already produced (each one just
a bag of cell names) and the Design's netlist, it answers
"which macros does this net actually touch" and folds that
down into a flat MacroNetlist, ignoring any net that is fully
local to a single macro (that net has zero effect on macro-
level placement -- it would just be noise for
TimingDrivenFloorplanner / ClockRegionPlanner to look at).

Bit-id graph, briefly:
    Module.nets[i]        .bits = [3, 4]          (a 2-bit net)
    Module.cells[j].connections = {"Y": [3]}       (this cell's
                                                     Y pin sits
                                                     on bit 3,
                                                     i.e. it's on
                                                     that net)
So bit id is the join key between a net and the cells wired to
it -- there is no direct cell<->net field in the Yosys JSON
schema, which is why this lookup has to go through bit ids.
=========================================================
"""

from collections import defaultdict

from backend.floorplanning.models import MacroNet, MacroNetlist


# ==========================================================
# NET NAME -> KIND HEURISTIC
# ==========================================================
# Same spirit as macro_classifier.py: a coarse, name-based
# bucket, good enough for floorplan-stage decisions (should
# TimingDrivenFloorplanner pull this net's macros together
# harder, should ClockRegionPlanner treat it as a clock tree).
# A real flow would get this from SDC create_clock / a
# clock-tree spec instead of guessing from the string.
# ==========================================================

CLOCK_KEYWORDS = ("CLK", "CLOCK", "PCLK", "SCLK")
RESET_KEYWORDS = ("RST", "RESET", "RSTN", "RST_N")


def _classify_net(net_name):

    n = str(net_name).upper()

    for kw in CLOCK_KEYWORDS:
        if kw in n:
            return "clock"

    for kw in RESET_KEYWORDS:
        if kw in n:
            return "reset"

    return "data"


class NetlistConnectivity:
    """
    module  : a backend.floorplanning.design.Module (has
              .cells with .connections, and .nets with .bits)
    macros  : the List[Macro] MacroBuilder already produced
              (each Macro.cells is a list of cell names)
    """

    def __init__(self, module, macros):

        self.module = module

        self.macros = macros

    # ------------------------------------------------------
    # bit id -> net name
    # ------------------------------------------------------

    def _build_bit_to_net(self):

        bit_to_net = {}

        for net in getattr(self.module, "nets", []) or []:

            for bit in net.bits:

                # A constant bit ("0"/"1"/"x"/"z" in Yosys JSON,
                # or any non-hashable/duplicate marker) can't
                # anchor real connectivity between macros --
                # skip anything that isn't a plain int bit id.
                if not isinstance(bit, int):
                    continue

                bit_to_net[bit] = net.name

        return bit_to_net

    # ------------------------------------------------------
    # cell name -> macro name
    # ------------------------------------------------------

    def _build_cell_to_macro(self):

        cell_to_macro = {}

        for macro in self.macros:

            for cell_name in macro.cells:

                cell_to_macro[cell_name] = macro.name

        return cell_to_macro

    # ------------------------------------------------------
    # net name -> {macro_name: pin_count}
    # ------------------------------------------------------

    def _build_net_to_macro_pins(self, bit_to_net, cell_to_macro):

        net_to_macro_pins = defaultdict(lambda: defaultdict(int))

        for cell in getattr(self.module, "cells", []) or []:

            macro_name = cell_to_macro.get(cell.name)

            if macro_name is None:
                # Cell wasn't grouped into any macro (shouldn't
                # happen if macros were built from this same
                # module's cells, but a partial/filtered cell
                # list is a legitimate caller pattern) -- skip.
                continue

            seen_nets_for_cell = set()

            for _port, bits in (cell.connections or {}).items():

                for bit in bits:

                    net_name = bit_to_net.get(bit)

                    if net_name is None:
                        continue

                    # Count each net once per cell (not once per
                    # bit/pin) -- a multi-bit bus pin shouldn't
                    # get N times the weight of a 1-bit control
                    # pin just because it has more wires.
                    if net_name in seen_nets_for_cell:
                        continue

                    seen_nets_for_cell.add(net_name)

                    net_to_macro_pins[net_name][macro_name] += 1

        return net_to_macro_pins

    # ------------------------------------------------------

    def build(self):

        if self.module is None or not self.macros:
            return MacroNetlist(nets=[])

        bit_to_net = self._build_bit_to_net()

        cell_to_macro = self._build_cell_to_macro()

        net_to_macro_pins = self._build_net_to_macro_pins(
            bit_to_net, cell_to_macro
        )

        macro_nets = []

        for net_name, macro_pins in net_to_macro_pins.items():

            # Only nets that actually span 2+ macros matter at
            # macro-level -- a net fully contained in one
            # macro's cell list has no bearing on macro
            # placement.
            if len(macro_pins) < 2:
                continue

            weight = float(sum(macro_pins.values()))

            macro_nets.append(
                MacroNet(
                    name=net_name,
                    kind=_classify_net(net_name),
                    macros=sorted(macro_pins.keys()),
                    weight=weight,
                )
            )

        # Deterministic ordering (dict iteration order isn't
        # guaranteed across Yosys JSON dumps) so downstream
        # output (JSON export, renderer) is stable run-to-run.
        macro_nets.sort(key=lambda n: n.name)

        return MacroNetlist(nets=macro_nets)
