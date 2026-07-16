from graphviz import Digraph
import re
import os

# =========================================================
# PATH SETUP
# =========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))
STATIC_PATH = os.path.join(PROJECT_ROOT, "static")

os.makedirs(STATIC_PATH, exist_ok=True)


# =========================================================
# RESERVED WORDS
# =========================================================
RESERVED = {
    "module", "endmodule", "input", "output", "wire",
    "reg", "assign", "always", "if", "else", "case",
    "begin", "end", "for", "generate"
}


# =========================================================
# PARSE ALL MODULES
# =========================================================
def parse_modules(code):
    """
    Extract all Verilog modules with their ports and body.
    """
    pattern = r'module\s+(\w+)\s*\((.*?)\);(.*?)endmodule'
    modules = {}

    for match in re.finditer(pattern, code, re.DOTALL):
        mod_name = match.group(1)
        ports = match.group(2)
        body = match.group(3)

        modules[mod_name] = {
            "ports": ports,
            "body": body
        }

    return modules


# =========================================================
# FIND TOP MODULE
# =========================================================
def find_top_module(modules):
    """
    Detect module not instantiated by others = top.
    """
    instantiated = set()

    for mod_data in modules.values():
        body = mod_data["body"]

        insts = re.findall(r'\b(\w+)\s+\w+\s*\(', body)

        for inst_mod in insts:
            if inst_mod in modules:
                instantiated.add(inst_mod)

    tops = [m for m in modules if m not in instantiated]

    return tops[-1] if tops else list(modules.keys())[0]


# =========================================================
# PORT EXTRACTION
# =========================================================
def extract_ports(port_text):
    inputs = re.findall(r'input\s+(?:\[\d+:\d+\]\s*)?(\w+)', port_text)
    outputs = re.findall(r'output\s+(?:\[\d+:\d+\]\s*)?(\w+)', port_text)

    return inputs, outputs


# =========================================================
# DRAW MODULE BLOCK
# =========================================================
def draw_module_block(dot, node_id, module_name, inputs, outputs):
    """
    Draw Vivado-style block with ports.
    """
    label = f"""<
    <TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="6">
        <TR>
            <TD BGCOLOR="#334155">
                <FONT COLOR="white"><B>{module_name}</B></FONT>
            </TD>
        </TR>
    """

    for i in inputs:
        label += f"""
        <TR>
            <TD ALIGN="LEFT">⬅ {i}</TD>
        </TR>
        """

    for o in outputs:
        label += f"""
        <TR>
            <TD ALIGN="RIGHT">{o} ➡</TD>
        </TR>
        """

    label += "</TABLE>>"

    dot.node(
        node_id,
        label=label,
        shape="plaintext"
    )


# =========================================================
# RECURSIVE HIERARCHY DRAWER
# =========================================================
def draw_hierarchy(dot, modules, module_name, parent=None, prefix=""):
    node_id = prefix + module_name

    inputs, outputs = extract_ports(modules[module_name]["ports"])

    draw_module_block(dot, node_id, module_name, inputs, outputs)

    if parent:
        dot.edge(parent, node_id)

    body = modules[module_name]["body"]

    instances = re.findall(r'\b(\w+)\s+(\w+)\s*\(', body)

    grouped = {}

    for child_mod, inst_name in instances:
        if child_mod in modules and child_mod not in RESERVED:
            grouped.setdefault(child_mod, []).append(inst_name)

    for child_mod, insts in grouped.items():

        # Compress repeated instances
        if len(insts) > 4:
            cluster_id = prefix + child_mod + "_cluster"

            dot.node(
                cluster_id,
                f"{child_mod}\\n×{len(insts)}",
                shape="box",
                style="filled,rounded",
                fillcolor="#475569",
                fontcolor="white"
            )

            dot.edge(node_id, cluster_id)

        else:
            for inst in insts:
                draw_hierarchy(
                    dot,
                    modules,
                    child_mod,
                    parent=node_id,
                    prefix=prefix + inst + "_"
                )


# =========================================================
# MAIN GENERATOR
# =========================================================
def generate_elaborate_design_diagram(code, filename="elaborate_design"):
    modules = parse_modules(code)

    if not modules:
        raise ValueError("No Verilog modules detected.")

    top_module = find_top_module(modules)

    dot = Digraph(format='png')

    dot.attr(
        rankdir='LR',
        splines='ortho',
        nodesep='1.0',
        ranksep='1.5',
        bgcolor="#0f172a"
    )

    draw_hierarchy(dot, modules, top_module)

    output_path = os.path.join(STATIC_PATH, filename)
    dot.render(output_path, cleanup=True)

    return f"{output_path}.png"
