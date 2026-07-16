import networkx as nx
from backend.rtl_parser_engine.logic_graph import LogicGraph


class CriticalPathAnalyzer:
    def __init__(self, filepath):
        self.filepath = filepath

    def analyze(self):
        graph_builder = LogicGraph(self.filepath)
        graph = graph_builder.build_graph()

        if not nx.is_directed_acyclic_graph(graph):
            return {
                "status": "warning",
                "message": "Graph contains cycles; critical path may be invalid."
            }

        longest_path = nx.dag_longest_path(graph)

        return {
            "status": "success",
            "critical_path": longest_path,
            "logic_depth": len(longest_path) - 1
        }