import os
import json
import re
import random

import networkx as nx
import plotly.graph_objects as go

from backend.Visualization.graph_utils import (
    create_timing_graph,
    get_node_positions,
    get_critical_edges
)


# ---------------------------------------------------
# RTL PARSER
# ---------------------------------------------------

def parse_rtl_file(verilog_file):

    with open(verilog_file, "r") as f:
        rtl = f.read()

    return rtl


# ---------------------------------------------------
# EXTRACT SIMPLE LOGIC OPERATIONS
# ---------------------------------------------------

def extract_logic_operations(rtl_text):

    operations = []

    gate_count = 1

    # ------------------------------------------
    # ASSIGN STATEMENTS
    # ------------------------------------------

    assign_lines = re.findall(
        r'assign\s+(.*?);',
        rtl_text
    )

    # ------------------------------------------
    # ALWAYS BLOCKS
    # ------------------------------------------

    always_blocks = re.findall(
        r'always\s*@\(.*?\)(.*?)end',
        rtl_text,
        re.DOTALL
    )

    all_logic = assign_lines + always_blocks

    for line in all_logic:

        line = line.lower()

        # --------------------------------------
        # AND
        # --------------------------------------

        for _ in range(line.count("&")):

            operations.append({
                "gate": f"AND_{gate_count}",
                "type": "AND"
            })

            gate_count += 1

        # --------------------------------------
        # OR
        # --------------------------------------

        for _ in range(line.count("|")):

            operations.append({
                "gate": f"OR_{gate_count}",
                "type": "OR"
            })

            gate_count += 1

        # --------------------------------------
        # XOR
        # --------------------------------------

        for _ in range(line.count("^")):

            operations.append({
                "gate": f"XOR_{gate_count}",
                "type": "XOR"
            })

            gate_count += 1

        # --------------------------------------
        # NOT
        # --------------------------------------

        for _ in range(line.count("~")):

            operations.append({
                "gate": f"NOT_{gate_count}",
                "type": "NOT"
            })

            gate_count += 1

        # --------------------------------------
        # ADDER
        # --------------------------------------

        for _ in range(line.count("+")):

            operations.append({
                "gate": f"ADD_{gate_count}",
                "type": "ADD"
            })

            gate_count += 1

        # --------------------------------------
        # SUBTRACTOR
        # --------------------------------------

        for _ in range(line.count("-")):

            operations.append({
                "gate": f"SUB_{gate_count}",
                "type": "SUB"
            })

            gate_count += 1

        # --------------------------------------
        # MULTIPLIER
        # --------------------------------------

        for _ in range(line.count("*")):

            operations.append({
                "gate": f"MUL_{gate_count}",
                "type": "MUL"
            })

            gate_count += 1

        # --------------------------------------
        # IF CONDITIONS
        # --------------------------------------

        if "if" in line:

            operations.append({
                "gate": f"MUX_{gate_count}",
                "type": "MUX"
            })

            gate_count += 1

        # --------------------------------------
        # CASE STATEMENTS
        # --------------------------------------

        if "case" in line:

            operations.append({
                "gate": f"CASE_{gate_count}",
                "type": "CASE"
            })

            gate_count += 1

        # --------------------------------------
        # REGISTER DETECTION
        # --------------------------------------

        if "<=" in line:

            operations.append({
                "gate": f"FF_{gate_count}",
                "type": "FF"
            })

            gate_count += 1

    # ------------------------------------------
    # DEFAULT FALLBACK
    # ------------------------------------------

    if len(operations) == 0:

        operations.append({
            "gate": "LOGIC_1",
            "type": "LOGIC"
        })

    return operations

# ---------------------------------------------------
# GENERATE TIMING GRAPH DATA
# ---------------------------------------------------

def generate_timing_data(operations):

    nodes = []
    edges = []

    critical_path = []

    # ----------------------------------------
    # INPUT NODE
    # ----------------------------------------

    nodes.append({

        "id": "INPUT",

        "stage": 0,

        "type": "IO"
    })

    current_stage = 1

    previous_stage_nodes = ["INPUT"]

    # ----------------------------------------
    # BUILD STAGE-WISE GRAPH
    # ----------------------------------------

    for op in operations:

        gate_name = op["gate"]

        gate_type = op["type"]

        # ------------------------------------
        # CREATE NODE
        # ------------------------------------

        nodes.append({

            "id": gate_name,

            "stage": current_stage,

            "type": gate_type
        })

        # ------------------------------------
        # CONNECT PREVIOUS STAGE
        # ------------------------------------

        source_node = random.choice(
            previous_stage_nodes
        )

        delay = round(
            random.uniform(0.1, 1.0),
            2
        )

        slack = round(
            random.uniform(-0.5, 5.0),
            2
        )

        edges.append({

            "from": source_node,

            "to": gate_name,

            "delay": delay,

            "slack": slack
        })

        # ------------------------------------
        # CRITICAL PATH TRACKING
        # ------------------------------------

        if random.random() > 0.4:

            critical_path.extend([

                source_node,

                gate_name
            ])

        # ------------------------------------
        # FF CREATES NEW PIPELINE STAGE
        # ------------------------------------

        if gate_type == "FF":

            current_stage += 1

            previous_stage_nodes = [gate_name]

        else:

            previous_stage_nodes.append(gate_name)

    # ----------------------------------------
    # OUTPUT NODE
    # ----------------------------------------

    nodes.append({

        "id": "OUTPUT",

        "stage": current_stage + 1,

        "type": "IO"
    })

    # ----------------------------------------
    # CONNECT FINAL STAGE TO OUTPUT
    # ----------------------------------------

    final_output_sources = previous_stage_nodes[-2:]

    for node in final_output_sources:

        delay = round(
            random.uniform(0.1, 1.0),
            2
        )

        slack = round(
            random.uniform(-0.5, 5.0),
            2
        )

        edges.append({

            "from": node,

            "to": "OUTPUT",

            "delay": delay,

            "slack": slack
        })

    # ----------------------------------------
    # FINAL CRITICAL PATH
    # ----------------------------------------

    critical_path.extend(previous_stage_nodes)

    critical_path.append("OUTPUT")

    # ----------------------------------------
    # RETURN GRAPH DATA
    # ----------------------------------------

    return {

        "nodes": nodes,

        "edges": edges,

        "critical_path": critical_path
    }


# ---------------------------------------------------
# SAVE JSON
# ---------------------------------------------------

def save_timing_json(data, output_file):

    with open(output_file, "w") as f:
        json.dump(data, f, indent=4)


# ---------------------------------------------------
# LOAD JSON
# ---------------------------------------------------

def load_timing_data(json_file):

    with open(json_file, "r") as f:
        data = json.load(f)

    return data


# ---------------------------------------------------
# GENERATE VISUALIZATION
# ---------------------------------------------------
def get_slack_color(slack):

    if slack < 0:

        return "red"

    elif slack < 1.0:

        return "orange"

    elif slack < 2.5:

        return "yellow"

    else:

        return "lime"

def generate_timing_figure(data):

    nodes = data["nodes"]
    edges = data["edges"]
    critical_path = data["critical_path"]

    G = create_timing_graph(nodes, edges)

    pos = get_node_positions(G)

    critical_edges = get_critical_edges(critical_path)

    edge_x = []
    edge_y = []

    critical_x = []
    critical_y = []

    for edge in G.edges():

        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]

        if edge in critical_edges:

            critical_x.extend([x0, x1, None])
            critical_y.extend([y0, y1, None])

        else:

            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

    # NORMAL EDGES
    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,

        line=dict(
            width=2,
            color='gray',
            shape='spline'
        ),

        hoverinfo='none',

        mode='lines'
    )

    # CRITICAL PATH
    critical_trace = go.Scatter(
        x=critical_x,
        y=critical_y,

        line=dict(
            width=6,
            color='red',
            shape='spline',
            dash='solid'
        ),

        hoverinfo='none',

        mode='lines'
    )

    # NODES
    node_x = []
    node_y = []
    node_text = []

    for node in G.nodes():

        x, y = pos[node]

        node_x.append(x)
        node_y.append(y)
        node_text.append(node)

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode='markers+text',
        text=node_text,
        textposition="bottom center",
        hovertemplate=
        """
        Gate: %{text}<extra></extra>
        """,
        marker=dict(
            size=22,
            color=[
                'red' if 'AND' in node else
                'orange' if 'OR' in node else
                'purple' if 'XOR' in node else
                'green' if 'ADD' in node else
                'cyan'
                for node in G.nodes()
            ],
            symbol=[
                'square' if 'FF' in node else
                'diamond' if 'MUX' in node else
                'hexagon' if 'MUL' in node else
                'circle'
                for node in G.nodes()
            ],
            
            line_width=2
        )
    )

    fig = go.Figure(
        data=[
            edge_trace,
            critical_trace,
            node_trace
        ]
    )
    
    # =================================================
    # SLACK-COLORED EDGE TRACES
    # =================================================

    for edge in G.edges():

        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]

        slack = G.edges[edge]["slack"]

        edge_color = get_slack_color(slack)

        fig.add_trace(

            go.Scatter(

                x=[x0, x1],
                y=[y0, y1],

                mode='lines',

                line=dict(
                    width=3,
                    color=edge_color,
                    shape='spline'
                ),

                hovertemplate=
                """
                Gate: %{text}<extra></extra>
                """,

                text=f"Slack: {slack}ns"
            )
        )
        
        
    
    # =================================================
    # EDGE DELAY LABELS
    # =================================================

    for edge in G.edges():

        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]

        delay = G.edges[edge]["delay"]

        mid_x = (x0 + x1) / 2
        mid_y = (y0 + y1) / 2

        fig.add_annotation(

            x=mid_x,
            y=mid_y,

            text=f"{delay}ns",

            showarrow=False,

            font=dict(
                color="yellow",
                size=10
            )
        )
    
    
    for edge in G.edges():

        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]

        fig.add_annotation(

            ax=x0,
            ay=y0,
            x=x1,
            y=y1,

            xref='x',
            yref='y',
            axref='x',
            ayref='y',

            showarrow=True,

            arrowhead=3,

            arrowsize=1,

            arrowwidth=1.5,

            arrowcolor="gray"
        )

    fig.update_layout(
        title="AIEDA Timing Path Visualization",
        showlegend=False,
        hovermode='closest',
        margin=dict(b=20, l=20, r=20, t=50),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            visible=False
        ),

        yaxis=dict(
            showgrid=False,
            zeroline=False,
            visible=False
        ),
        template="plotly_dark",
        plot_bgcolor='black',
        paper_bgcolor='black',
    )

    return fig