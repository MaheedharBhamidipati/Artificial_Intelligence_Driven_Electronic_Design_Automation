"""
===========================================================
Connectivity Engine
===========================================================
"""

from backend.graph.graph_builder import GraphBuilder

from backend.graph.graph_metrics import GraphMetrics

from backend.graph.graph_visualizer import (
    GraphVisualizer
)


class ConnectivityEngine:

    def __init__(

        self,

        design

    ):

        self.design = design

    def run(self):

        graph = GraphBuilder(

            self.design

        ).build()

        metrics = GraphMetrics(

            graph

        ).calculate()

        GraphVisualizer().save(

            graph,

            "outputs/connectivity_graph.png"
        )

        return {

            "graph": graph,

            "metrics": metrics
        }