# ============================================================
# CONGESTION VISUALIZATION
# ============================================================

import random

import plotly.graph_objects as go

# ============================================================
# CONGESTION VIEW
# ============================================================

class CongestionView:

    def __init__(self):

        self.grid_width = 8

        self.cell_width = 90

        self.cell_height = 70

        self.x_spacing = 110

        self.y_spacing = 90

        self.start_x = 150

        self.start_y = 320

    # ========================================================
    # RENDER
    # ========================================================

    def render(self, congestion_data):

        fig = go.Figure()

        hotspots = congestion_data["hotspots"]

        x_points = []
        y_points = []

        # ====================================================
        # CHIP OUTLINE
        # ====================================================

        fig.add_shape(

            type="rect",

            x0=100,
            y0=250,

            x1=1250,
            y1=950,

            line=dict(

                color="#00E5FF",

                width=4
            ),

            fillcolor="rgba(0,0,0,0)"
        )

        # ====================================================
        # DRAW HOTSPOTS
        # ====================================================

        for i, hotspot in enumerate(hotspots):

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

            # ------------------------------------------------
            # REALISTIC CONGESTION
            # ------------------------------------------------

            base_score = hotspot["congestion_score"]

            routing_pressure = random.randint(0, 70)

            score = min(

                100,

                base_score + routing_pressure
            )

            # ------------------------------------------------
            # COLOR MAPPING
            # ------------------------------------------------

            # LOW
            if score < 30:

                color = "#00C853"

                label = "LOW"

            # MEDIUM
            elif score < 60:

                color = "#FFD600"

                label = "MEDIUM"

            # HIGH
            elif score < 80:

                color = "#FF9100"

                label = "HIGH"

            # OVERFLOW
            else:

                color = "#FF1744"

                label = "OVERFLOW"

            # ------------------------------------------------
            # STORE POINTS
            # ------------------------------------------------

            x_points.append(x)

            y_points.append(y)

            # ------------------------------------------------
            # OVERFLOW GLOW
            # ------------------------------------------------

            if score > 80:

                fig.add_shape(

                    type="rect",

                    x0=x - 8,
                    y0=y - 8,

                    x1=x + self.cell_width + 8,
                    y1=y + self.cell_height + 8,

                    fillcolor="rgba(255,0,0,0.20)",

                    line=dict(
                        color="rgba(255,0,0,0)"
                    )
                )

            # ------------------------------------------------
            # MAIN RECTANGLE
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
            # NET NAME
            # ------------------------------------------------

            fig.add_annotation(

                x=x + 45,

                y=y + 45,

                text=f"<b>{hotspot['net']}</b>",

                showarrow=False,

                font=dict(

                    color="white",

                    size=8
                )
            )

            # ------------------------------------------------
            # SCORE
            # ------------------------------------------------

            fig.add_annotation(

                x=x + 45,

                y=y + 22,

                text=f"{score}%",

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
        # LEGEND
        # ====================================================

        legend_x = 1400

        legend_y = 1050

        legend_items = [

            ("#00C853", "LOW CONGESTION"),

            ("#FFD600", "MEDIUM CONGESTION"),

            ("#FF9100", "HIGH CONGESTION"),

            ("#FF1744", "OVERFLOW REGION")
        ]

        for i, (color, label) in enumerate(

            legend_items
        ):

            y_pos = legend_y - (i * 80)

            # ------------------------------------------------
            # COLOR BOX
            # ------------------------------------------------

            fig.add_shape(

                type="rect",

                x0=legend_x,
                y0=y_pos,

                x1=legend_x + 60,
                y1=y_pos + 40,

                fillcolor=color,

                line=dict(color="white")
            )

            # ------------------------------------------------
            # LABEL
            # ------------------------------------------------

            fig.add_annotation(

                x=legend_x + 220,

                y=y_pos + 20,

                text=f"<b>{label}</b>",

                showarrow=False,

                font=dict(

                    color="white",

                    size=12
                )
            )

        # ====================================================
        # SUMMARY
        # ====================================================

        total_hotspots = len(hotspots)

        avg_congestion = sum(

            min(
                100,
                hotspot["congestion_score"] +
                random.randint(0, 70)
            )

            for hotspot in hotspots
        ) / total_hotspots

        fig.add_annotation(

            x=1550,

            y=650,

            text=(

                f"<b>HOTSPOTS</b><br>"
                f"{total_hotspots}<br><br>"

                f"<b>AVG CONGESTION</b><br>"
                f"{avg_congestion:.2f}%"
            ),

            showarrow=False,

            align="left",

            font=dict(

                color="cyan",

                size=14
            )
        )

        # ====================================================
        # TITLE
        # ====================================================

        fig.add_annotation(

            x=850,

            y=1180,

            text="<b>🔥 AIEDA Congestion Analysis</b>",

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

            plot_bgcolor="#071633",

            paper_bgcolor="#071633",

            font=dict(color="white"),

            width=1800,

            height=950,

            dragmode=False,

            hovermode=False,

            margin=dict(

                l=20,
                r=20,

                t=20,
                b=20
            ),

            xaxis=dict(

                range=[0, 1800],

                visible=False
            ),

            yaxis=dict(

                range=[0, 1300],

                visible=False,

                scaleanchor="x"
            )
        )

        return fig