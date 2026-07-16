import os
import re
from graphviz import Digraph


# ============================================================
# STATE EXTRACTION
# ============================================================

def extract_states(verilog_code):

    states = []

    # parameter S0=0,S1=1,S2=2;
    for match in re.findall(
        r'(?:parameter|localparam)\s+([^;]+);',
        verilog_code,
        re.IGNORECASE
    ):

        names = re.findall(
            r'([A-Za-z_][A-Za-z0-9_]*)\s*=',
            match
        )

        states.extend(names)

    # enum support
    enum_match = re.search(
        r'typedef\s+enum.*?\{(.*?)\}',
        verilog_code,
        re.DOTALL
    )

    if enum_match:

        enum_body = enum_match.group(1)

        enum_states = re.findall(
            r'([A-Za-z_][A-Za-z0-9_]*)',
            enum_body
        )

        states.extend(enum_states)

    unique_states = []

    for s in states:

        if s not in unique_states:
            unique_states.append(s)

    return unique_states

# ============================================================
# TRANSITION EXTRACTION
# ============================================================

# ============================================================
# TRANSITION EXTRACTION
# ============================================================

def extract_transitions(verilog_code):

    transitions = []

    # ========================================================
    # CASE-BASED FSMs
    # ========================================================

    case_matches = re.finditer(
        r'case\s*\(\s*\w+\s*\)(.*?)endcase',
        verilog_code,
        re.DOTALL | re.IGNORECASE
    )

    for case_match in case_matches:

        case_body = case_match.group(1)

        state_blocks = re.findall(
            r'([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*?)(?=\n\s*[A-Za-z_][A-Za-z0-9_]*\s*:|\Z)',
            case_body,
            re.DOTALL
        )

        for current_state, block in state_blocks:

            if current_state.lower() == "default":
                continue

            # ------------------------------------------------
            # if (...) next_state/state <= TARGET
            # ------------------------------------------------

            conditional_matches = re.findall(
                r'if\s*\((.*?)\).*?(?:next_state|state)\s*(?:<=|=)\s*([A-Za-z_][A-Za-z0-9_]*)',
                block,
                re.DOTALL
            )

            for condition, next_state in conditional_matches:

                transitions.append({
                    "from": current_state,
                    "to": next_state,
                    "condition": condition.strip()
                })

            # ------------------------------------------------
            # else next_state/state <= TARGET
            # ------------------------------------------------

            else_matches = re.findall(
                r'else\s*.*?(?:next_state|state)\s*(?:<=|=)\s*([A-Za-z_][A-Za-z0-9_]*)',
                block,
                re.DOTALL
            )

            for next_state in else_matches:

                transitions.append({
                    "from": current_state,
                    "to": next_state,
                    "condition": "else"
                })

            # ------------------------------------------------
            # direct assignment
            # next_state = S1;
            # next_state <= S1;
            # state = S1;
            # state <= S1;
            # ------------------------------------------------

            direct_matches = re.findall(
                r'(?:next_state|state)\s*(?:<=|=)\s*([A-Za-z_][A-Za-z0-9_]*)',
                block
            )

            for next_state in direct_matches:

                already_exists = any(
                    t["from"] == current_state and
                    t["to"] == next_state
                    for t in transitions
                )

                if not already_exists:

                    transitions.append({
                        "from": current_state,
                        "to": next_state,
                        "condition": ""
                    })

    # ========================================================
    # NESTED IF FSM SUPPORT
    # ========================================================

    nested_if_matches = re.findall(
        r'if\s*\(\s*state\s*==\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)(.*?)(?=else\s+if|else|\Z)',
        verilog_code,
        re.DOTALL
    )

    for current_state, block in nested_if_matches:

        next_states = re.findall(
            r'(?:next_state|state)\s*(?:<=|=)\s*([A-Za-z_][A-Za-z0-9_]*)',
            block
        )

        for next_state in next_states:

            already_exists = any(
                t["from"] == current_state and
                t["to"] == next_state
                for t in transitions
            )

            if not already_exists:

                transitions.append({
                    "from": current_state,
                    "to": next_state,
                    "condition": ""
                })

    # ========================================================
    # REMOVE DUPLICATES
    # ========================================================

    unique_transitions = []

    seen = set()

    for t in transitions:

        key = (
            t["from"],
            t["to"],
            t["condition"]
        )

        if key not in seen:

            seen.add(key)

            unique_transitions.append(t)

    return unique_transitions
# ============================================================
# FSM SUMMARY
# ============================================================

def generate_fsm_summary(states, transitions):

    return {
        "total_states": len(states),
        "total_transitions": len(transitions),
        "states": states
    }


# ============================================================
# FSM GRAPH
# ============================================================



def generate_fsm_graph(states, transitions):

    dot = Digraph("FSM")

    dot.attr(rankdir="LR")
    dot.attr(fontsize="12")
    dot.attr(
        labelloc="t"
    )

    dot.attr(
        label=
        "Green = Initial | Blue = Normal | Orange = Self-Loop | Red = Terminal"
    )

    initial_state = (
        states[0]
        if states
        else None
    )

    source_states = {
        t["from"]
        for t in transitions
    }

    destination_states = {
        t["to"]
        for t in transitions
    }

    # ==========================================
    # TERMINAL STATES
    # ==========================================

    terminal_states = set()

    for state in states:

        outgoing = [

            t

            for t in transitions

            if t["from"] == state
            and t["to"] != state

        ]

        if len(outgoing) == 0:

            terminal_states.add(
                state
            )
    
    # ==========================================
    # SELF LOOP STATES
    # ==========================================

    self_loop_states = set()

    for transition in transitions:

        if transition["from"] == transition["to"]:

            self_loop_states.add(
                transition["from"]
            )

    for state in states:

        if state == initial_state:
            fillcolor = "lightgreen"

        elif state in terminal_states:
            fillcolor = "lightcoral"

        elif state in self_loop_states:
            fillcolor = "orange"

        else:
            fillcolor = "lightblue"

        dot.node(
            state,
            shape="circle",
            style="filled",
            fillcolor=fillcolor
        )

    for transition in transitions:

        dot.edge(
            transition["from"],
            transition["to"],
            label=transition["condition"]
        )

    project_root = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            ".."
        )
    )

    generated_dir = os.path.join(
        project_root,
        "static",
        "generated"
    )

    os.makedirs(
        generated_dir,
        exist_ok=True
    )

    output_path = os.path.join(
        generated_dir,
        "fsm"
    )

    print("\n========================")
    print("FSM OUTPUT PATH:")
    print(output_path)
    print("========================\n")

    dot.render(
        output_path,
        format="svg",
        cleanup=True
    )

    svg_file = output_path + ".svg"

    print(
        "FSM SVG EXISTS:",
        os.path.exists(svg_file)
    )

    return (
        "/static/generated/fsm.svg"
    )

# ============================================================
# MAIN API
# ============================================================

def extract_fsm(verilog_code):

    states = extract_states(verilog_code)

    print("\nFSM STATES FOUND:")
    print(states)

    transitions = extract_transitions(verilog_code)

    print("\nFSM TRANSITIONS FOUND:")
    print(transitions)

    fsm_svg = generate_fsm_graph(
        states,
        transitions
    )

    summary = generate_fsm_summary(
        states,
        transitions
    )

    return {
        "fsm_svg": fsm_svg,
        "states": states,
        "transitions": transitions,
        "summary": summary
    }