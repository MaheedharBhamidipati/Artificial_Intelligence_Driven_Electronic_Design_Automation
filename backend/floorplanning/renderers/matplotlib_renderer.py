"""
==========================================================
AIDEA Floorplanning

Matplotlib Renderer

Creates textbook-style floorplans.

Author : AIDEA
==========================================================
"""

import os

import matplotlib.pyplot as plt

import matplotlib.patches as patches

from backend.floorplanning.utils import get_color


class MatplotlibRenderer:

    def __init__(self):

        pass

    # =====================================================

    def render(

        self,

        chip,

        output_file

    ):

        fig, ax = plt.subplots(

            figsize=(12,8)

        )

        ax.set_xlim(

            0,

            chip.width

        )

        ax.set_ylim(

            0,

            chip.height

        )

        ax.set_aspect("equal")

        ax.axis("off")

        # -------------------------------------------------
        # CHIP
        # -------------------------------------------------

        chip_box = patches.Rectangle(

            (0,0),

            chip.width,

            chip.height,

            linewidth=3,

            edgecolor="black",

            facecolor="#F8F9FA"

        )

        ax.add_patch(chip_box)

        # -------------------------------------------------
        # CORE
        # -------------------------------------------------

        core = patches.Rectangle(

            (

                chip.core_margin,

                chip.core_margin

            ),

            chip.width-2*chip.core_margin,

            chip.height-2*chip.core_margin,

            linewidth=2,

            linestyle="--",

            edgecolor="#444",

            facecolor="#FFFFFF"

        )

        ax.add_patch(core)

        # -------------------------------------------------
        # TITLE
        # -------------------------------------------------

        ax.text(

            chip.width/2,

            chip.height+2,

            "AIDEA FLOORPLAN",

            ha="center",

            fontsize=16,

            fontweight="bold"

        )

        # -------------------------------------------------
        # CONGESTION HEATMAP (drawn first, as a background wash
        # under everything else -- it's a density estimate over
        # the whole core, not a discrete object like a macro or
        # a stripe, so it shouldn't visually compete with them)
        # -------------------------------------------------

        if getattr(chip, "congestion_map", None) is not None:

            for congestion_bin in chip.congestion_map.bins:

                # Green (low) -> yellow -> red (>= hotspot
                # threshold), clamped so a very high ratio still
                # just reads as "fully red" rather than blowing
                # out the color math.
                level = min(congestion_bin.congestion, 1.0)

                heat_color = (
                    min(1.0, 2 * level),
                    min(1.0, 2 * (1 - level)),
                    0.0,
                )

                ax.add_patch(
                    patches.Rectangle(
                        (congestion_bin.x, congestion_bin.y),
                        congestion_bin.width,
                        congestion_bin.height,
                        linewidth=0.3,
                        edgecolor="#FFFFFF",
                        facecolor=heat_color,
                        alpha=0.30 if not congestion_bin.hotspot else 0.55,
                        zorder=-1,
                    )
                )

        # -------------------------------------------------
        # POWER PLAN (drawn before macros so macros sit on top)
        # -------------------------------------------------

        net_colors = {"VDD": "#E53935", "VSS": "#1E88E5"}

        if getattr(chip, "power_plan", None) is not None:

            for stripe in chip.power_plan.stripes:

                ax.add_patch(
                    patches.Rectangle(
                        (stripe.x, stripe.y),
                        stripe.width,
                        stripe.height,
                        linewidth=0,
                        facecolor=net_colors.get(stripe.net, "#999999"),
                        alpha=0.35,
                        zorder=1,
                    )
                )

            for ring in chip.power_plan.rings:

                ax.add_patch(
                    patches.Rectangle(
                        (ring.x, ring.y),
                        ring.width,
                        ring.height,
                        linewidth=ring.ring_width,
                        edgecolor=net_colors.get(ring.net, "#999999"),
                        facecolor="none",
                        alpha=0.8,
                        zorder=2,
                    )
                )

            for via in chip.power_plan.vias:

                ax.plot(
                    via.x,
                    via.y,
                    marker="x",
                    markersize=3,
                    color=net_colors.get(via.net, "#999999"),
                    alpha=0.5,
                    zorder=3,
                )

        # -------------------------------------------------
        # PLACEMENT BLOCKAGES
        # -------------------------------------------------

        if getattr(chip, "blockage_plan", None) is not None:

            for blockage in chip.blockage_plan.placement_blockages:

                if blockage.kind != "hard":
                    continue

                ax.add_patch(
                    patches.Rectangle(
                        (blockage.x, blockage.y),
                        blockage.width,
                        blockage.height,
                        hatch="xx",
                        linewidth=0,
                        facecolor="#B0BEC5",
                        alpha=0.35,
                        zorder=0,
                    )
                )

        # -------------------------------------------------
        # POWER DOMAINS
        # -------------------------------------------------

        if getattr(chip, "power_domain_plan", None) is not None:

            domain_palette = ["#8E24AA", "#00897B", "#FB8C00", "#3949AB", "#7CB342"]

            for idx, domain in enumerate(chip.power_domain_plan.domains):

                ax.add_patch(
                    patches.Rectangle(
                        (domain.x, domain.y),
                        domain.width,
                        domain.height,
                        linewidth=1.5,
                        linestyle=":",
                        edgecolor=domain_palette[idx % len(domain_palette)],
                        facecolor="none",
                        alpha=0.9,
                        zorder=4,
                    )
                )

                ax.text(
                    domain.x + 1,
                    domain.y + domain.height - 2,
                    f"{domain.name}",
                    fontsize=7,
                    color=domain_palette[idx % len(domain_palette)],
                    zorder=4,
                )

            boundary_markers = {"level_shifter": "D", "isolation": "s"}

            for cell in chip.power_domain_plan.boundary_cells:

                ax.plot(
                    cell.x,
                    cell.y,
                    marker=boundary_markers.get(cell.kind, "o"),
                    markersize=6,
                    markerfacecolor="yellow",
                    markeredgecolor="black",
                    zorder=5,
                )

        # -------------------------------------------------
        # MACRO NET CONNECTIVITY (drawn before macros, like the
        # power plan, so the macro rectangles + labels sit on
        # top and stay readable). Only present when
        # NetlistConnectivity actually ran -- absent chips (no
        # netlist_module supplied) skip this block entirely.
        # -------------------------------------------------

        if getattr(chip, "macro_netlist", None) is not None and chip.macro_netlist.nets:

            macro_centers = {
                m.name: (m.x + m.width / 2.0, m.y + m.height / 2.0)
                for m in chip.macros
            }

            max_weight = max(
                (n.weight for n in chip.macro_netlist.nets), default=1.0
            ) or 1.0

            net_line_colors = {
                "clock": "#FB8C00",
                "reset": "#8E24AA",
                "data": "#546E7A",
            }

            for net in chip.macro_netlist.nets:

                members = [
                    macro_centers[name]
                    for name in net.macros
                    if name in macro_centers
                ]

                if len(members) < 2:
                    continue

                # Star topology from the first member so an
                # N-way net draws as N-1 segments instead of a
                # dense N-choose-2 tangle.
                hub = members[0]

                for other in members[1:]:

                    ax.plot(
                        [hub[0], other[0]],
                        [hub[1], other[1]],
                        color=net_line_colors.get(net.kind, "#546E7A"),
                        linewidth=0.6 + 2.4 * (net.weight / max_weight),
                        alpha=0.35 if net.kind == "data" else 0.6,
                        zorder=3.5,
                        solid_capstyle="round",
                    )

        # -------------------------------------------------
        # MACROS
        # -------------------------------------------------

        for macro in chip.macros:

            rect = patches.Rectangle(

                (

                    macro.x,

                    macro.y

                ),

                macro.width,

                macro.height,

                facecolor=get_color(

                    macro.macro_type

                ),

                edgecolor="black",

                linewidth=2

            )

            ax.add_patch(rect)

            label = macro.name

            if getattr(macro, "orientation", "N") != "N":

                label = f"{macro.name}\n[{macro.orientation}]"

            ax.text(

                macro.x+macro.width/2,

                macro.y+macro.height/2,

                label,

                ha="center",

                va="center",

                fontsize=8,

                fontweight="bold"

            )

        # -------------------------------------------------
        # CLOCK REGIONS (drawn on top of macros, distinct
        # dash-dot style from power domains' dotted style so the
        # two derived-region overlays stay visually separable)
        # -------------------------------------------------

        if getattr(chip, "clock_plan", None) is not None and chip.clock_plan.regions:

            clock_color = "#FB8C00"

            for region in chip.clock_plan.regions:

                pad = 0.6

                ax.add_patch(
                    patches.Rectangle(
                        (region.x - pad, region.y - pad),
                        region.width + 2 * pad,
                        region.height + 2 * pad,
                        linewidth=1.6,
                        linestyle="-.",
                        edgecolor=clock_color,
                        facecolor="none",
                        alpha=0.9,
                        zorder=6,
                    )
                )

                ax.text(
                    region.x - pad,
                    region.y + region.height + pad + 0.8,
                    f"CLK: {region.clock_net}",
                    fontsize=7,
                    color=clock_color,
                    fontweight="bold",
                    zorder=6,
                )

        # -------------------------------------------------
        # STANDARD CELL REGION
        # -------------------------------------------------

        if chip.standard_cells:

            region = chip.standard_cells

            rect = patches.Rectangle(

                (

                    region.x,

                    region.y

                ),

                region.width,

                region.height,

                facecolor="#EEEEEE",

                edgecolor="#888",

                hatch="////"

            )

            ax.add_patch(rect)

            ax.text(

                region.x+region.width/2,

                region.y+region.height/2,

                "STANDARD CELL REGION",

                ha="center",

                fontsize=11,

                fontweight="bold"

            )

        # -------------------------------------------------
        # INPUTS
        # -------------------------------------------------

        ax.text(

            2,

            chip.height-3,

            "INPUTS",

            fontsize=10,

            fontweight="bold",

            color="green"

        )

        # -------------------------------------------------
        # OUTPUTS
        # -------------------------------------------------

        ax.text(

            chip.width-16,

            2,

            "OUTPUTS",

            fontsize=10,

            fontweight="bold",

            color="red"

        )

        # -------------------------------------------------
        # LEGEND
        # -------------------------------------------------

        legend_x = chip.width+2

        legend_y = chip.height-10

        for macro in chip.macros:

            ax.add_patch(

                patches.Rectangle(

                    (

                        legend_x,

                        legend_y

                    ),

                    3,

                    3,

                    facecolor=get_color(

                        macro.macro_type

                    )

                )

            )

            ax.text(

                legend_x+4,

                legend_y+1.5,

                macro.macro_type,

                fontsize=8,

                va="center"

            )

            legend_y-=5

        plt.savefig(

            output_file,

            dpi=250,

            bbox_inches="tight"

        )

        plt.close()