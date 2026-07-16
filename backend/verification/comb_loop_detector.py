import networkx as nx
from backend.rtl_parser_engine.logic_graph import LogicGraph


class CombLoopDetector:
    def __init__(self, filepath):
        self.filepath = filepath

    def detect(self):
        graph = LogicGraph(self.filepath).build_graph()

        try:
            cycle = nx.find_cycle(graph, orientation="original")
            return {
                "has_loop": True,
                "cycle": cycle
            }
        except:
            return {
                "has_loop": False
            }