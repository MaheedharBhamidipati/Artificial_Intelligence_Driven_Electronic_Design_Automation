"""
=========================================================
AIDEA FLOORPLANNER

Routing Blockage Manager

A placed hard macro doesn't just block *placement* under
itself -- it physically blocks *routing* on every metal
layer at or below wherever its own pins land, because
there's silicon/lower-metal already used up under the
macro's footprint. Real flows generate this "macro shadow"
automatically; this file is that step for AIDEA.

Distinct from placement_blockage_manager.py on purpose:
placement blockages stop the PLACER from putting a macro
somewhere; routing blockages stop the ROUTER from running a
wire somewhere. A macro produces both, but they're different
tools' concerns (and a real DEF file keeps them in separate
sections), so they stay in separate managers/lists here too.
=========================================================
"""

from backend.floorplanning.models import RoutingBlockage


class RoutingBlockageManager:

    def __init__(self, chip, blocked_layers=("M1", "M2", "M3")):

        self.chip = chip

        self.blocked_layers = blocked_layers

    # ------------------------------------------------------

    def _macro_shadow_blockages(self):

        blockages = []

        for macro in self.chip.macros:

            for layer in self.blocked_layers:

                blockages.append(
                    RoutingBlockage(
                        layer=layer,
                        x=macro.x,
                        y=macro.y,
                        width=macro.width,
                        height=macro.height,
                        source="macro_shadow",
                    )
                )

        return blockages

    # ------------------------------------------------------

    def generate(self, extra_blockages=None):

        blockages = self._macro_shadow_blockages()

        blockages.extend(extra_blockages or [])

        return blockages
