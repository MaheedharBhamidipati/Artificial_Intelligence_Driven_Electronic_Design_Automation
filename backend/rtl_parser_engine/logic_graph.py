import networkx as nx
from .gate_mapper import GateMapper


class LogicGraph:

    def __init__(self, filepath):

        self.filepath = filepath

        self.graph = nx.DiGraph()

    def build_graph(self):

        mapper = GateMapper(self.filepath)

        gates = mapper.map_gates()

        for gate in gates:

            gate_node = gate["gate_id"]

            self.graph.add_node(
                gate_node,
                gate_type=gate["gate_type"]
            )

            for inp in gate["inputs"]:

                self.graph.add_node(inp, node_type="signal")

                self.graph.add_edge(inp, gate_node)

            self.graph.add_node(
                gate["output"],
                node_type="signal"
            )

            self.graph.add_edge(gate_node, gate["output"])

        return self.graph

    def print_graph(self):

        print("\nLogic Connections:\n")

        for edge in self.graph.edges():
            print(f"{edge[0]} ---> {edge[1]}")


if __name__ == "__main__":

    lg = LogicGraph("example.v")

    lg.build_graph()

    lg.print_graph()
