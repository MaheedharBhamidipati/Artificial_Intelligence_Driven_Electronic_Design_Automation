# ================================================================
# TIMING GRAPH BUILDER
# ================================================================


class TimingGraphBuilder:

    def __init__(

        self,

        timing_paths
    ):

        self.paths = timing_paths

    # ============================================================
    # BUILD GRAPH
    # ============================================================

    def build_graph(self):

        nodes = []

        edges = []

        node_set = set()

        for path in self.paths:

            src = path.get(

                "startpoint",

                "START"
            )

            dst = path.get(

                "endpoint",

                "END"
            )

            if src not in node_set:

                nodes.append({

                    "data": {

                        "id": src,

                        "label": src
                    }
                })

                node_set.add(src)

            if dst not in node_set:

                nodes.append({

                    "data": {

                        "id": dst,

                        "label": dst
                    }
                })

                node_set.add(dst)

            edges.append({

                "data": {

                    "source": src,

                    "target": dst,

                    "slack": path.get(

                        "slack",

                        0.0
                    ),

                    "status": path.get(

                        "status",

                        "SAFE"
                    )
                }
            })

        return {

            "nodes": nodes,

            "edges": edges
        }