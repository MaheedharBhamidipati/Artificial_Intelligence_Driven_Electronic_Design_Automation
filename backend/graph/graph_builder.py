"""
===========================================================
AIDEA Graph Builder
===========================================================
"""

import networkx as nx


class GraphBuilder:

    def __init__(self, design):

        self.design = design

    def build(self):

        graph = nx.DiGraph()

        for module in self.design.modules:

            for cell in module.cells:

                graph.add_node(
                    cell.name,
                    type=cell.cell_type
                )

            #
            # Create connectivity
            #

            net_driver = {}

            for cell in module.cells:

                for port, bits in cell.connections.items():

                    for bit in bits:

                        bit = str(bit)

                        if port.upper() in (
                            "Y",
                            "Q",
                            "O",
                            "OUT"
                        ):

                            net_driver[bit] = cell.name

            for cell in module.cells:

                for port, bits in cell.connections.items():

                    for bit in bits:

                        bit = str(bit)

                        if bit in net_driver:

                            src = net_driver[bit]

                            dst = cell.name

                            if src != dst:

                                graph.add_edge(src, dst)

        return graph