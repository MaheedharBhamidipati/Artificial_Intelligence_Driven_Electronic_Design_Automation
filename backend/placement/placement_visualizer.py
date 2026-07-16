# ============================================================
# FILE: backend/placement/placement_visualizer.py
# ============================================================

import plotly.graph_objects as go


def visualize_placement(blocks):

    fig = go.Figure()

    # ========================================================
    # DRAW BLOCKS
    # ========================================================

    for block in blocks:

        x = block["x"]
        y = block["y"]

        width = block["w"]
        height = block["h"]

        color = block["color"]

        node = block["name"]

        # ====================================================
        # RECTANGLE
        # ====================================================

        fig.add_shape(

            type="rect",

            x0=x,
            y0=y,

            x1=x + width,
            y1=y + height,

            line=dict(
                color="white",
                width=1
            ),

            fillcolor=color
        )

        # ====================================================
        # LABEL FILTERING
        # ====================================================

        if len(blocks) < 50:

            fig.add_trace(

                go.Scatter(

                    x=[x + width / 2],

                    y=[y + height / 2],

                    text=[

                        node[:10]

                        if len(node) > 10

                        else node
                    ],

                    mode="text",

                    textfont=dict(

                        color="white",

                        size=10
                    ),

                    showlegend=False
                )
            )

    # ========================================================
    # FORCE AXIS RANGE
    # ========================================================

    fig.update_xaxes(

        range=[0, 1800]
    )

    fig.update_yaxes(

        range=[0, 1800]
    )

    # ========================================================
    # LAYOUT
    # ========================================================

    fig.update_layout(

        title="AIDEA Placement Visualization",

        paper_bgcolor="black",
        plot_bgcolor="black",

        font=dict(color="white"),

        width=1400,
        height=800,

        xaxis=dict(

            showgrid=True,
            gridcolor="gray",

            zeroline=False
        ),

        yaxis=dict(

            showgrid=True,
            gridcolor="gray",

            zeroline=False,

            scaleanchor="x",
            scaleratio=1
        )
    )
    
    
    # ========================================================
    # LEGEND
    # ========================================================

    legend_items = [

        ("FF / DFF", "yellow"),
        ("Logic Cells", "gray"),
        ("ADD Units", "green"),
        ("MUL Units", "orange"),
        ("MUX Units", "purple"),
        ("INPUT / OUTPUT", "cyan")
    ]

    legend_x = 1550
    legend_y = 1600

    for index, (label, color) in enumerate(legend_items):

        y_pos = legend_y - (index * 80)

        # ----------------------------------------------------
        # COLOR BOX
        # ----------------------------------------------------

        fig.add_shape(

            type="rect",

            x0=legend_x,
            y0=y_pos,

            x1=legend_x + 50,
            y1=y_pos + 50,

            fillcolor=color,

            line=dict(
                color="white"
            )
        )

        # ----------------------------------------------------
        # LABEL
        # ----------------------------------------------------

        fig.add_trace(

            go.Scatter(

                x=[legend_x + 120],

                y=[y_pos + 25],

                text=[label],

                mode="text",

                textfont=dict(

                    color="white",

                    size=14
                ),

                showlegend=False
            )
        )

    return fig