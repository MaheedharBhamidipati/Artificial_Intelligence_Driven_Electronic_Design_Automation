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
# UTILITIES
# =========================================================
def extract_top_module(code):
    modules = re.findall(r'\bmodule\s+(\w+)', code)
    return modules[-1] if modules else "TOP"


def extract_ports(code, module):
    pattern = rf'module\s+{module}\s*\((.*?)\);'
    match = re.search(pattern, code, re.DOTALL)

    if not match:
        return [], []

    port_block = match.group(1)

    inputs = re.findall(r'input\s+(?:\[\d+:\d+\]\s*)?(\w+)', port_block)
    outputs = re.findall(r'output\s+(?:\[\d+:\d+\]\s*)?(\w+)', port_block)

    return inputs, outputs


# =========================================================
# OPERATOR TO GATE NAME
# =========================================================
def operator_to_gate(expr):
    if '&' in expr:
        return "AND"
    elif '|' in expr:
        return "OR"
    elif '^' in expr:
        return "XOR"
    elif '~' in expr:
        return "NOT"
    elif '+' in expr:
        return "ADD"
    elif '-' in expr:
        return "SUB"
    elif '*' in expr:
        return "MUL"
    elif '/' in expr:
        return "DIV"
    elif '?' in expr and ':' in expr:
        return "MUX"
    return "LOGIC"


# =========================================================
# ASSIGN / COMBINATIONAL LOGIC VIEW
# =========================================================
def draw_assign_logic(dot, code):
    assigns = re.findall(r'assign\s+(\w+)\s*=\s*(.*?);', code)

    for idx, (out, expr) in enumerate(assigns):

        gate_type = operator_to_gate(expr)
        gate_id = f"{gate_type}_{idx}"

        dot.node(
            gate_id,
            gate_type,
            shape="box",
            style="filled,rounded",
            fillcolor="#0f766e",
            fontcolor="white"
        )

        signals = re.findall(r'\b[a-zA-Z_]\w*\b', expr)

        for sig in signals:
            if sig != out:
                dot.node(sig, sig, shape="circle", width="0.4")
                dot.edge(sig, gate_id)

        dot.node(out, out, shape="circle", width="0.4")
        dot.edge(gate_id, out)


# =========================================================
# CONSOLIDATED SEQUENTIAL VIEW
# =========================================================
def draw_sequential_logic(dot, code):
    always_blocks = re.findall(r'always\s*@\s*\((.*?)\)', code)

    if not always_blocks:
        return

    # Determine label intelligently
    if "case" in code.lower():
        block_label = "FSM"
    elif "counter" in code.lower():
        block_label = "COUNTER"
    else:
        block_label = "REG / FSM"

    dot.node(
        "SEQ_BLOCK",
        block_label,
        shape="box",
        style="filled,rounded",
        fillcolor="#ea580c",
        fontcolor="white"
    )

    clock_added = False
    reset_added = False

    for sens in always_blocks:
        signals = re.findall(r'\b[a-zA-Z_]\w*\b', sens)

        for sig in signals:
            sig_l = sig.lower()

            if ("clk" in sig_l or "clock" in sig_l) and not clock_added:
                dot.node("clk", "clk", shape="circle", width="0.5")
                dot.edge("clk", "SEQ_BLOCK")
                clock_added = True

            elif ("rst" in sig_l or "reset" in sig_l) and not reset_added:
                dot.node("rst", "rst", shape="circle", width="0.5")
                dot.edge("rst", "SEQ_BLOCK")
                reset_added = True


# =========================================================
# FALLBACK BLOCK VIEW
# =========================================================
def draw_block_view(dot, module, inputs, outputs):
    dot.node(
        module,
        module.upper(),
        shape="box",
        style="filled,rounded",
        fillcolor="#1e293b",
        fontcolor="white"
    )

    for i in inputs:
        dot.node(i, i, shape="circle", width="0.4")
        dot.edge(i, module)

    for o in outputs:
        dot.node(o, o, shape="circle", width="0.4")
        dot.edge(module, o)


# =========================================================
# MAIN GENERATOR
# =========================================================
def generate_basic_circuit_diagram(code, filename="circuit"):
    dot = Digraph(format='png')

    dot.attr(
        rankdir='LR',
        splines='ortho',
        nodesep='0.8',
        ranksep='1.0',
        bgcolor="#0f172a"
    )

    module = extract_top_module(code)
    inputs, outputs = extract_ports(code, module)

    has_assign = bool(re.search(r'\bassign\b', code))
    has_always = bool(re.search(r'\balways\b', code))

    if has_assign:
        draw_assign_logic(dot, code)

    if has_always:
        draw_sequential_logic(dot, code)

    if not has_assign and not has_always:
        draw_block_view(dot, module, inputs, outputs)

    output_path = os.path.join(STATIC_PATH, filename)
    dot.render(output_path, cleanup=True)

    return f"{output_path}.png"
