from graphviz import Digraph
import re
import os

RUNS_PATH = "D:/AI_EDA_TOOL/runs/"
STATIC_PATH = "D:/AI_EDA_TOOL/static"


def generate_netlist_diagram():
    """
    Convert synthesized netlist into gate-level diagram
    """

    netlist_file = RUNS_PATH + "netlist.v"

    if not os.path.exists(netlist_file):
        print("❌ Netlist not found")
        return None

    with open(netlist_file, "r") as f:
        code = f.read()

    dot = Digraph(format="png")
    dot.attr(rankdir="LR")

    # -----------------------------------------
    # Extract gate instantiations
    # -----------------------------------------
    gates = re.findall(r'(\w+)\s+(\w+)\s*\((.*?)\);', code, re.DOTALL)

    for gate_type, inst_name, connections in gates:
        dot.node(inst_name, gate_type)

        # Extract signals
        ports = re.findall(r'\.(\w+)\((.*?)\)', connections)

        for port, signal in ports:
            signal = signal.strip()

            # Create signal nodes
            dot.node(signal, signal, shape="box")

            # Connect
            dot.edge(signal, inst_name)

    # -----------------------------------------
    # Save
    # -----------------------------------------
    output_path = os.path.join(STATIC_PATH, "netlist")

    dot.render(output_path, cleanup=True)

    print(f"✅ Netlist diagram saved: {output_path}.png")

    return f"{output_path}.png"
