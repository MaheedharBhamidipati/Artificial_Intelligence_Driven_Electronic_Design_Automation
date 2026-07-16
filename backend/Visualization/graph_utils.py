import networkx as nx


def create_timing_graph(nodes, edges):

    G = nx.DiGraph()

    # ----------------------------------------
    # ADD NODES WITH STAGES
    # ----------------------------------------

    for node in nodes:

        G.add_node(

            node["id"],

            stage=node.get("stage", 0),

            gate_type=node.get("type", "LOGIC")
        )

    # ----------------------------------------
    # ADD EDGES
    # ----------------------------------------

    for edge in edges:

        G.add_edge(

            edge["from"],

            edge["to"],

            delay=edge.get("delay", 0),

            slack=edge.get("slack", 0)
        )

    return G


def get_node_positions(G):

    pos = {}

    # ----------------------------------------
    # GROUP NODES BY STAGE
    # ----------------------------------------

    stage_groups = {}

    for node, data in G.nodes(data=True):

        stage = data.get("stage", 0)

        if stage not in stage_groups:

            stage_groups[stage] = []

        stage_groups[stage].append(node)

    # ----------------------------------------
    # SORT STAGES
    # ----------------------------------------

    sorted_stages = sorted(stage_groups.keys())

    # ----------------------------------------
    # EDA-LIKE LEFT-RIGHT FLOW
    # ----------------------------------------

    x_spacing = 6
    y_spacing = 2

    for stage_index, stage in enumerate(sorted_stages):

        node_list = stage_groups[stage]

        total_nodes = len(node_list)

        # CENTER ALIGNMENT
        center_offset = (total_nodes - 1) / 2

        for i, node in enumerate(node_list):

            x = stage_index * x_spacing

            y = (center_offset - i) * y_spacing

            pos[node] = (x, y)

    return pos


def get_critical_edges(critical_path):
    """
    Convert critical path node list into edge tuples.
    """

    critical_edges = []

    for i in range(len(critical_path) - 1):
        critical_edges.append(
            (critical_path[i], critical_path[i + 1])
        )

    return critical_edges

