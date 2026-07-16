from graphviz import Digraph
import re
import os

# =========================================================
# 📁 PATH (ROBUST)
# =========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))
STATIC_PATH = os.path.join(PROJECT_ROOT, "static")

os.makedirs(STATIC_PATH, exist_ok=True)


# =========================================================
# 🧠 FSM GENERATOR (PROFESSIONAL)
# =========================================================
def generate_fsm_diagram(code, filename="fsm"):

    dot = Digraph(format='png')
    dot.attr(rankdir='LR', bgcolor="#0d1117")

    # =====================================================
    # 🎨 STYLE
    # =====================================================
    dot.attr('node',
             shape='circle',
             style='filled',
             fontname="Helvetica",
             fontsize='11',
             color="#58a6ff",
             fillcolor="#1f6feb",
             fontcolor="white")

    dot.attr('edge',
             fontname="Helvetica",
             fontsize='10',
             color="#8b949e")

    # =====================================================
    # 1️⃣ FIND STATE VARIABLE
    # =====================================================
    state_var = "state"

    match = re.search(r'case\s*\(\s*(\w+)\s*\)', code)
    if match:
        state_var = match.group(1)

    # =====================================================
    # 2️⃣ STATE ENCODING DETECTION (FIXED 🔥)
    # =====================================================
    encoding = "UNKNOWN"

    if re.search(r"\b\d+'b[01]+\b", code):
        encoding = "BINARY"

    if re.search(r"parameter\s+\w+\s*=\s*\d+'b1\b", code):
        encoding = "ONE-HOT"

    if re.search(r"\btypedef\s+enum\b|\benum\b", code):
        encoding = "ENUM"

    # =====================================================
    # 3️⃣ EXTRACT CASE BLOCK
    # =====================================================
    case_block_match = re.search(
        rf'case\s*\(\s*{state_var}\s*\)(.*?)endcase',
        code,
        re.DOTALL | re.IGNORECASE
    )

    if not case_block_match:
        print("❌ No FSM detected")
        return None

    case_block = case_block_match.group(1)

    # =====================================================
    # 4️⃣ STATES
    # =====================================================
    state_names = re.findall(r'(\w+)\s*:', case_block)
    states = sorted({s for s in state_names if s.lower() != "default"})

    if not states:
        print("❌ No states found")
        return None

    # =====================================================
    # 5️⃣ TRANSITIONS (FIXED)
    # =====================================================
    transitions = set()

    state_cases = re.findall(
        r'(\w+)\s*:\s*(.*?)(?=\w+\s*:|default\s*:|$)',
        case_block,
        re.DOTALL
    )

    mealy_flag = False

    for state, logic in state_cases:

        # 🔥 Better Mealy detection
        if re.search(r'<=\s*\w+', logic) and not re.search(rf'{state_var}\s*<=', logic):
            mealy_flag = True

        # IF transitions
        for cond, nxt in re.findall(
            rf'if\s*\((.*?)\)\s*.*?{state_var}\s*<=\s*(\w+)',
            logic,
            re.DOTALL
        ):
            transitions.add((state, nxt, cond.strip()))

        # ELSE transitions
        for nxt in re.findall(
            rf'else\s+{state_var}\s*<=\s*(\w+)',
            logic
        ):
            transitions.add((state, nxt, "else"))

        # DIRECT transitions (avoid duplicates)
        for nxt in re.findall(
            rf'{state_var}\s*<=\s*(\w+)',
            logic
        ):
            transitions.add((state, nxt, ""))

    # =====================================================
    # 6️⃣ FSM TYPE
    # =====================================================
    fsm_type = "MEALY" if mealy_flag else "MOORE"

    # =====================================================
    # 7️⃣ RESET DETECTION (FIXED)
    # =====================================================
    reset_state = None

    reset_match = re.search(
        rf'if\s*\(\s*(rst|reset).*?\)\s*{state_var}\s*<=\s*(\w+)',
        code,
        re.IGNORECASE
    )

    if reset_match:
        reset_state = reset_match.group(2)

    # =====================================================
    # 8️⃣ STATE REGISTER BLOCK
    # =====================================================
    dot.node("STATE_REG",
             f"State Register\n({encoding})",
             shape="box",
             fillcolor="#238636",
             color="#2ea043")

    # =====================================================
    # 9️⃣ DRAW STATES
    # =====================================================
    for s in states:
        if s == reset_state:
            dot.node(s,
                     shape='doublecircle',
                     fillcolor="#d73a49",
                     label=f"{s}\nRESET")
        else:
            dot.node(s)

        dot.edge("STATE_REG", s, style="dotted")

    # =====================================================
    # 🔟 DRAW TRANSITIONS
    # =====================================================
    for src, dst, cond in transitions:

        if src not in states or dst not in states:
            continue

        label = cond if cond else ""

        if src == dst:
            dot.edge(src, dst, label=label,
                     color="#d29922", style="dashed")
        else:
            dot.edge(src, dst, label=label)

    # =====================================================
    # 1️⃣1️⃣ TITLE
    # =====================================================
    with dot.subgraph(name="cluster_title") as c:
        c.attr(
            label=f"FSM ({fsm_type}) | Encoding: {encoding}",
            color="white"
        )

    # =====================================================
    # 💾 SAVE
    # =====================================================
    output_path = os.path.join(STATIC_PATH, filename)
    dot.render(output_path, cleanup=True)

    print(f"✅ FSM diagram saved: {output_path}.png")

    return f"{output_path}.png"
