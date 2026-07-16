# ================================================================
# RTL FLOW ROUTER
# ================================================================

class RTLFlowRouter:

    def __init__(self, dot):

        self.dot = dot

    # ============================================================
    # GENERIC ROUTER
    # ============================================================

    def route(

        self,

        src,

        dst,

        color="black",

        style="solid",

        penwidth="1.5"
    ):

        if src == dst:

            return

        self.dot.edge(

            src,

            dst,

            color=color,

            style=style,

            penwidth=str(penwidth),

            arrowhead="vee",

            arrowsize="0.7",

            constraint="true"
        )

    # ============================================================
    # INPUT ROUTING
    # ============================================================

    def route_input(

        self,

        src,

        dst,

        color,

        style,

        penwidth
    ):

        self.route(

            src,

            dst,

            color,

            style,

            penwidth
        )

    # ============================================================
    # OUTPUT ROUTING
    # ============================================================

    def route_output(

        self,

        src,

        dst,

        color,

        style,

        penwidth
    ):

        self.route(

            src,

            dst,

            color,

            style,

            penwidth
        )

    # ============================================================
    # INTERNAL ROUTING
    # ============================================================

    def route_internal(

        self,

        src,

        dst,

        color,

        style,

        penwidth
    ):

        self.route(

            src,

            dst,

            color,

            style,

            penwidth
        )