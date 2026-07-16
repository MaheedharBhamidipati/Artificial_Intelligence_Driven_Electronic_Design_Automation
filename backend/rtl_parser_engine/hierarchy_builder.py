import networkx as nx
from .rtl_parser import RTLParser


class HierarchyBuilder:

    def __init__(self, filepath):

        self.filepath = filepath

        self.graph = nx.DiGraph()

        self.modules = []

    def build(self):

        parser = RTLParser(self.filepath)

        parser.parse_file()

        self.modules = parser.extract_modules()

        for module in self.modules:

            parent = module["module_name"]

            self.graph.add_node(parent)

            for inst in module["instances"]:

                child = inst["module_type"]

                self.graph.add_edge(parent, child)

        return self.graph

    def print_hierarchy(self):

        print("\nModule Hierarchy:\n")

        for edge in self.graph.edges():
            print(f"{edge[0]} ---> {edge[1]}")


if __name__ == "__main__":

    builder = HierarchyBuilder("example.v")

    builder.build()

    builder.print_hierarchy()
