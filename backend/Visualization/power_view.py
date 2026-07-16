# ============================================================
# POWER VISUALIZATION
# ============================================================

import random

import plotly.graph_objects as go

from backend.Visualization.shared_plot_utils import (

    apply_dark_theme,

    set_title,

    style_axes,

    power_color
)

# ============================================================
# POWER VIEW
# ============================================================

class PowerView:

    def __init__(self):

        # ----------------------------------------------------
        # GRID CONFIGURATION
        # ----------------------------------------------------

        self.grid_width = 10

        self.cell_width = 100

        self.cell_height = 70

        self.x_spacing = 130

        self.y_spacing = 100

        self.start_x = 150

        self.start_y = 350

    # ========================================================
    # POWER RENDER
    # ========================================================

    def render(self, power_cells):

        fig = go.Figure()

        x_points = []
        y_points = []

        # ====================================================
        # CHIP OUTLINE
        # ====================================================

        fig.add_shape(

            type="rect",

            x0=100,
            y0=300,

            x1=1450,
            y1=900,

            line=dict(

                color="#00E5FF",

                width=4
            ),

            fillcolor="rgba(0,0,0,0)"
        )

        # ====================================================
        # DRAW POWER CELLS
        # ====================================================

        for i, cell in enumerate(power_cells):

            # ------------------------------------------------
            # GRID POSITION
            # ------------------------------------------------

            x = (

                self.start_x +

                (i % self.grid_width)

                * self.x_spacing
            )

            y = (

                self.start_y +

                (i // self.grid_width)

                * self.y_spacing
            )

            power = cell["power"]

            # ------------------------------------------------
            # POWER COLOR MAPPING
            # ------------------------------------------------

            # LOW POWER
            if power < 25:

                color = "#1E90FF"

                power_level = "LOW"

            # NORMAL
            elif power < 50:

                color = "#00C853"

                power_level = "NORMAL"

            # MODERATE
            elif power < 75:

                color = "#FFD600"

                power_level = "MODERATE"

            # HOTSPOT
            else:

                color = "#FF1744"

                power_level = "HOTSPOT"

            # ------------------------------------------------
            # STORE POINTS
            # ------------------------------------------------

            x_points.append(x)

            y_points.append(y)

            # ------------------------------------------------
            # HOTSPOT GLOW
            # ------------------------------------------------

            if power > 75:

                fig.add_shape(

                    type="rect",

                    x0=x - 8,
                    y0=y - 8,

                    x1=x + self.cell_width + 8,
                    y1=y + self.cell_height + 8,

                    fillcolor="rgba(255,0,0,0.18)",

                    line=dict(
                        color="rgba(255,0,0,0)"
                    )
                )

            # ------------------------------------------------
            # POWER RECTANGLE
            # ------------------------------------------------

            fig.add_shape(

                type="rect",

                x0=x,
                y0=y,

                x1=x + self.cell_width,
                y1=y + self.cell_height,

                fillcolor=color,

                line=dict(

                    color="white",

                    width=2
                )
            )

            # ------------------------------------------------
            # CELL LABEL
            # ------------------------------------------------

            fig.add_annotation(

                x=x + (self.cell_width / 2),

                y=y + 42,

                text=f"<b>{cell['cell']}</b>",

                showarrow=False,

                font=dict(

                    color="white",

                    size=8
                )
            )

            # ------------------------------------------------
            # POWER VALUE
            # ------------------------------------------------

            fig.add_annotation(

                x=x + (self.cell_width / 2),

                y=y + 22,

                text=f"{power:.2f}W",

                showarrow=False,

                font=dict(

                    color="white",

                    size=7
                )
            )

        # ====================================================
        # INVISIBLE TRACE
        # ====================================================

        fig.add_trace(

            go.Scatter(

                x=x_points,
                y=y_points,

                mode="markers",

                marker=dict(

                    opacity=0
                ),

                showlegend=False
            )
        )

        # ====================================================
        # POWER LEGEND
        # ====================================================

        legend_x = 1520

        legend_y = 1000

        legend_items = [

            ("#1E90FF", "LOW POWER", "0W - 25W"),

            ("#00C853", "NORMAL POWER", "25W - 50W"),

            ("#FFD600", "MODERATE POWER", "50W - 75W"),

            ("#FF1744", "HOTSPOT / HIGH POWER", "> 75W")
        ]

        for i, (color, label, range_text) in enumerate(

            legend_items
        ):

            y_pos = legend_y - (i * 90)

            # ------------------------------------------------
            # LEGEND BOX
            # ------------------------------------------------

            fig.add_shape(

                type="rect",

                x0=legend_x,
                y0=y_pos,

                x1=legend_x + 60,
                y1=y_pos + 40,

                fillcolor=color,

                line=dict(

                    color="white",

                    width=1
                )
            )

            # ------------------------------------------------
            # LEGEND TEXT
            # ------------------------------------------------

            fig.add_annotation(

                x=legend_x + 220,

                y=y_pos + 20,

                text=(

                    f"<b>{label}</b><br>"
                    f"{range_text}"
                ),

                showarrow=False,

                align="left",

                font=dict(

                    color="white",

                    size=11
                )
            )

        # ====================================================
        # POWER SUMMARY
        # ====================================================

        total_power = sum(

            cell["power"]

            for cell in power_cells
        )

        avg_power = (

            total_power /

            len(power_cells)
        )

        fig.add_annotation(

            x=1620,

            y=580,

            text=(

                f"<b>TOTAL POWER</b><br>"
                f"{total_power:.2f} W<br><br>"

                f"<b>AVG POWER</b><br>"
                f"{avg_power:.2f} W"
            ),

            showarrow=False,

            align="left",

            font=dict(

                color="cyan",

                size=14
            )
        )

        # ====================================================
        # TITLE LABEL
        # ====================================================

        fig.add_annotation(

            x=850,

            y=1180,

            text="<b>⚡ AIEDA Physical Power Analysis</b>",

            showarrow=False,

            font=dict(

                color="white",

                size=24
            )
        )

        # ====================================================
        # LAYOUT
        # ====================================================

        fig.update_layout(

            # ------------------------------------------------
            # BACKGROUND
            # ------------------------------------------------

            plot_bgcolor="#071633",

            paper_bgcolor="#071633",

            font=dict(

                color="white"
            ),

            # ------------------------------------------------
            # SIZE
            # ------------------------------------------------

            width=1850,

            height=1000,

            # ------------------------------------------------
            # INTERACTION
            # ------------------------------------------------

            dragmode=False,

            hovermode=False,

            # ------------------------------------------------
            # MARGINS
            # ------------------------------------------------

            margin=dict(

                l=20,
                r=20,

                t=20,
                b=20
            ),

            # ------------------------------------------------
            # X AXIS
            # ------------------------------------------------

            xaxis=dict(

                range=[0, 1850],

                visible=False
            ),

            # ------------------------------------------------
            # Y AXIS
            # ------------------------------------------------

            yaxis=dict(

                range=[0, 1300],

                visible=False,

                scaleanchor="x"
            )
        )

        return fig

    # ========================================================
    # GENERATE SAMPLE DATA
    # ========================================================

    def generate_sample_cells(

        self,

        total_cells=50
    ):

        cells = []

        for i in range(total_cells):

            cells.append({

                "cell": f"CELL_{i}",

                "power": round(

                    random.uniform(5, 100),

                    2
                )
            })

        return cells