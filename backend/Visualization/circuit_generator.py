from graphviz import Digraph
import re
import os

# =========================================================
# PATH SETUP
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(BASE_DIR)
)

STATIC_PATH = os.path.join(
    PROJECT_ROOT,
    "static"
)

os.makedirs(
    STATIC_PATH,
    exist_ok=True
)

# =========================================================
# SANITIZE GRAPHVIZ NAMES
# =========================================================

def sanitize_name(name):

    name = str(name)

    # Replace invalid graphviz chars
    name = re.sub(
        r'[^a-zA-Z0-9_]',
        '_',
        name
    )

    # Graphviz IDs cannot start with numbers
    if name and name[0].isdigit():

        name = "N_" + name

    return name


# =========================================================
# UTILITIES
# =========================================================

def extract_top_module(code):

    modules = re.findall(
        r'\bmodule\s+(\w+)',
        code
    )

    return modules[-1] if modules else "TOP"


def extract_ports(code, module):

    pattern = rf'module\s+{module}\s*\((.*?)\);'

    match = re.search(
        pattern,
        code,
        re.DOTALL
    )

    if not match:
        return [], []

    port_block = match.group(1)

    inputs = re.findall(
        r'input\s+(?:\[\d+:\d+\]\s*)?(\w+)',
        port_block
    )

    outputs = re.findall(
        r'output\s+(?:\[\d+:\d+\]\s*)?(\w+)',
        port_block
    )

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

    assigns = re.findall(
        r'assign\s+(\w+)\s*=\s*(.*?);',
        code
    )

    input_nodes = set()
    output_nodes = set()

    # =====================================================
    # CREATE GATES
    # =====================================================

    for idx, (out, expr) in enumerate(assigns):

        gate_type = operator_to_gate(expr)

        gate_id = sanitize_name(
            f"{gate_type}_{idx}"
        )

        dot.node(
            gate_id,
            gate_type,
            shape="box",
            style="filled,rounded",
            fillcolor="#0f766e",
            fontcolor="white"
        )

        # -------------------------------------------------
        # INPUT SIGNALS
        # -------------------------------------------------

        signals = re.findall(
            r'\b[a-zA-Z_]\w*\b',
            expr
        )

        for sig in signals:

            if sig != out:

                safe_sig = sanitize_name(sig)

                input_nodes.add((safe_sig, sig))

                dot.edge(
                    safe_sig,
                    gate_id
                )

        # -------------------------------------------------
        # OUTPUT SIGNAL
        # -------------------------------------------------

        safe_out = sanitize_name(out)

        output_nodes.add((safe_out, out))

        dot.edge(
            gate_id,
            safe_out
        )

    # =====================================================
    # FORCE INPUTS TO LEFT
    # =====================================================

    with dot.subgraph() as s:

        s.attr(rank='same')

        for safe_sig, label in input_nodes:

            s.node(
                safe_sig,
                label,
                shape="circle",
                width="0.4"
            )

    # =====================================================
    # FORCE OUTPUTS TO RIGHT
    # =====================================================

    with dot.subgraph() as s:

        s.attr(rank='same')

        for safe_out, label in output_nodes:

            s.node(
                safe_out,
                label,
                shape="circle",
                width="0.4"
            )


# =========================================================
# SEQUENTIAL LOGIC VIEW
# =========================================================

def draw_sequential_logic(dot, code):

    always_blocks = re.findall(
        r'always\s*@\s*\((.*?)\)',
        code
    )

    if not always_blocks:
        return

    # =====================================================
    # Detect Sequential Type
    # =====================================================

    if "case" in code.lower():

        block_label = "FSM"

    elif "counter" in code.lower():

        block_label = "COUNTER"

    elif re.search(r'\bif\b', code):

        block_label = "REGISTER"

    else:

        block_label = "SEQ LOGIC"

    seq_block = sanitize_name("SEQ_BLOCK")

    dot.node(
        seq_block,
        block_label,
        shape="box",
        style="filled,rounded",
        fillcolor="#ea580c",
        fontcolor="white"
    )

    clock_added = False
    reset_added = False

    # =====================================================
    # Sensitivity List Parsing
    # =====================================================

    for sens in always_blocks:

        signals = re.findall(
            r'\b[a-zA-Z_]\w*\b',
            sens
        )

        for sig in signals:

            sig_l = sig.lower()

            safe_sig = sanitize_name(sig)

            # -------------------------------------------------
            # CLOCK
            # -------------------------------------------------

            if (
                "clk" in sig_l or
                "clock" in sig_l
            ) and not clock_added:

                dot.node(
                    safe_sig,
                    sig,
                    shape="circle",
                    width="0.5"
                )

                dot.edge(
                    safe_sig,
                    seq_block
                )

                clock_added = True

            # -------------------------------------------------
            # RESET
            # -------------------------------------------------

            elif (
                "rst" in sig_l or
                "reset" in sig_l
            ) and not reset_added:

                dot.node(
                    safe_sig,
                    sig,
                    shape="circle",
                    width="0.5"
                )

                dot.edge(
                    safe_sig,
                    seq_block
                )

                reset_added = True

    # =====================================================
    # Detect Registers
    # =====================================================

    regs = re.findall(
        r'reg\s+(?:\[\d+:\d+\]\s*)?(\w+)',
        code
    )

    for reg in regs:

        safe_reg = sanitize_name(reg)

        dot.node(
            safe_reg,
            reg,
            shape="ellipse",
            style="filled",
            fillcolor="#334155",
            fontcolor="white"
        )

        dot.edge(
            seq_block,
            safe_reg
        )


# =========================================================
# FALLBACK BLOCK VIEW
# =========================================================

def draw_block_view(
    dot,
    module,
    inputs,
    outputs
):

    safe_module = sanitize_name(module)

    dot.node(
        safe_module,
        module.upper(),
        shape="box",
        style="filled,rounded",
        fillcolor="#1e293b",
        fontcolor="white"
    )

    for i in inputs:

        safe_i = sanitize_name(i)

        dot.node(
            safe_i,
            i,
            shape="circle",
            width="0.4"
        )

        dot.edge(
            safe_i,
            safe_module
        )

    for o in outputs:

        safe_o = sanitize_name(o)

        dot.node(
            safe_o,
            o,
            shape="circle",
            width="0.4"
        )

        dot.edge(
            safe_module,
            safe_o
        )


# =========================================================
# MAIN GENERATOR
# =========================================================

def generate_basic_circuit_diagram(
    code,
    filename="circuit"
):

    dot = Digraph(format='png')

    dot.attr(

        rankdir='LR',

        splines='ortho',

        nodesep='1.0',

        ranksep='1.5',

        bgcolor="#0f172a"

    )

    dot.attr(

        'node',

        fontsize='12'
    )

    module = extract_top_module(code)

    inputs, outputs = extract_ports(
        code,
        module
    )

    has_assign = bool(
        re.search(r'\bassign\b', code)
    )

    has_always = bool(
        re.search(r'\balways\b', code)
    )

    # =====================================================
    # COMBINATIONAL
    # =====================================================

    if has_assign:

        draw_assign_logic(
            dot,
            code
        )

    # =====================================================
    # SEQUENTIAL
    # =====================================================

    if has_always:

        draw_sequential_logic(
            dot,
            code
        )

    # =====================================================
    # FALLBACK
    # =====================================================

    if not has_assign and not has_always:

        draw_block_view(
            dot,
            module,
            inputs,
            outputs
        )

    # =====================================================
    # OUTPUT
    # =====================================================

    output_path = os.path.join(
        STATIC_PATH,
        filename
    )

    dot.render(
        output_path,
        cleanup=True
    )

    return f"{output_path}.png"