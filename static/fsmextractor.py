from graphviz import Digraph
import re
import os

def generate_fsm_diagram(code, output_dir="output", filename="fsm_diagram"):
    """
    Robust FSM extractor for generic Verilog designs
    Supports multiple FSM coding styles
    """

    dot = Digraph(comment='FSM Diagram', format='png')
    dot.attr(rankdir='LR', dpi='300')
    dot.attr('node', shape='circle', style='filled', fillcolor='lightblue', fontname='Courier')

    # -------------------------------
    # 1. Extract STATES (robust)
    # -------------------------------
    state_patterns = [
        r'parameter\s+(\w+)\s*=',         
        r'localparam\s+(\w+)\s*=',        
        r'enum\s*\{([^}]+)\}',           
    ]

    states = set()

    for pattern in state_patterns:
        matches = re.findall(pattern, code, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            if isinstance(match, tuple):
                match = match[0]
            if ',' in match:  # enum case
                states.update([s.strip() for s in match.split(',')])
            else:
                states.add(match.strip())

    # Remove garbage tokens
    states = {s for s in states if len(s) > 1 and not s.lower() in ['state', 'next_state']}

    # -------------------------------
    # 2. Detect state register
    # -------------------------------
    state_var_match = re.search(r'(reg|logic)\s+\[.*?\]\s*(\w+)\s*,?\s*(\w+)?', code)
    state_var = None

    if state_var_match:
        state_var = state_var_match.group(2)

    if not state_var:
        state_var = "state"

    # -------------------------------
    # 3. Extract transitions (CASE)
    # -------------------------------
    transitions = []

    case_blocks = re.findall(r'case\s*\(\s*' + state_var + r'\s*\)(.*?)endcase',
                             code, re.DOTALL | re.IGNORECASE)

    for block in case_blocks:
        state_cases = re.findall(r'(\w+)\s*:\s*(.*?)(?=\w+\s*:|default\s*:|$)', block, re.DOTALL)

        for state, logic in state_cases:

            # Find next_state assignments
            next_matches = re.findall(r'(\w+)\s*<=\s*(\w+)', logic)

            for var, nxt in next_matches:
                if var in ['next_state', state_var]:
                    transitions.append((state, nxt, ""))

            # Detect IF conditions
            if_blocks = re.findall(r'if\s*\((.*?)\)\s*(\w+)\s*<=\s*(\w+)', logic)

            for cond, var, nxt in if_blocks:
                if var in ['next_state', state_var]:
                    transitions.append((state, nxt, cond.strip()))

    # -------------------------------
    # 4. Reset State Detection
    # -------------------------------
    reset_match = re.search(r'if\s*\(\s*rst.*?\)\s*' + state_var + r'\s*<=\s*(\w+)', code, re.IGNORECASE)
    reset_state = reset_match.group(1) if reset_match else None

    # -------------------------------
    # 5. Draw Nodes
    # -------------------------------
    for s in states:
        if s == reset_state:
            dot.node(s, shape='doublecircle', fillcolor='lightcoral')
        else:
            dot.node(s)

    # -------------------------------
    # 6. Draw Edges
    # -------------------------------
    for src, dst, cond in transitions:
        if src in states and dst in states:
            label = cond if cond else ""
            dot.edge(src, dst, label=label)

    # -------------------------------
    # 7. Output
    # -------------------------------
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)

    dot.render(output_path, cleanup=True)

    return f"{output_path}.png"
