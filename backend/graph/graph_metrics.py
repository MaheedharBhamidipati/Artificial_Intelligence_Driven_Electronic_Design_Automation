"""
===========================================================
Graph Metrics
===========================================================
"""

import networkx as nx


class GraphMetrics:

    def __init__(self, graph):

        self.graph = graph

    def calculate(self):

        return {

            "nodes":
                self.graph.number_of_nodes(),

            "edges":
                self.graph.number_of_edges(),

            "fanout":

                dict(self.graph.out_degree()),

            "fanin":

                dict(self.graph.in_degree())
        }