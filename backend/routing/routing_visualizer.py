# ============================================================
# ROUTING VISUALIZER
# ============================================================

import plotly.graph_objects as go


def visualize_routing(

    blocks,

    routes
):

    fig = go.Figure()

    # ========================================================
    # DRAW BLOCKS
    # ========================================================

    for block in blocks:

        fig.add_shape(

            type="rect",

            x0=block["x"],
            y0=block["y"],

            x1=block["x"] + block["w"],
            y1=block["y"] + block["h"],

            fillcolor=block["color"],

            line=dict(
                color="white"
            )
        )

    # ========================================================
    # DRAW ROUTES
    # ========================================================

    for route in routes:

        points = route["path"]

        x_points = [
            p[0]
            for p in points
        ]

        y_points = [
            p[1]
            for p in points
        ]

        fig.add_trace(

            go.Scatter(

                x=x_points,

                y=y_points,

                mode="lines",

                line=dict(

                    color="red",

                    width=3
                ),

                hovertext=

                f"{route['source']} → {route['target']}",

                showlegend=False
            )
        )

    # ========================================================
    # LAYOUT
    # ========================================================

    fig.update_layout(

        title="AIDEA Routing Visualization",

        paper_bgcolor="black",
        plot_bgcolor="black",

        font=dict(color="white"),

        width=1500,
        height=900
    )

    fig.update_xaxes(

        range=[0, 2000]
    )

    fig.update_yaxes(

        range=[0, 2000]
    )

    return fig