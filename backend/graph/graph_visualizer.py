"""
===========================================================
Graph Visualizer
===========================================================
"""

import matplotlib.pyplot as plt

import networkx as nx


class GraphVisualizer:

    def save(

        self,

        graph,

        filename

    ):

        plt.figure(

            figsize=(14,10)

        )

        pos = nx.spring_layout(

            graph,

            seed=42

        )

        nx.draw_networkx(

            graph,

            pos,

            with_labels=True,

            node_size=800,

            font_size=7,

            arrows=True

        )

        plt.tight_layout()

        plt.savefig(

            filename,

            dpi=300

        )

        plt.close()