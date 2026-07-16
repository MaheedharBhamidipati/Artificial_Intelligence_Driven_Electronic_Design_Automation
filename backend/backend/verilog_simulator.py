import re

# =========================================================
# 🔧 PARSER
# =========================================================

def parse_verilog(code):
    signals = {}
    assigns = []
    always_blocks = []

    # Parse input/output/wire/reg
    pattern = r"(input|output|wire|reg)\s*(\[[0-9:]+\])?\s*([^;]+);"
    matches = re.findall(pattern, code)

    for typ, width, names in matches:
        names = [n.strip() for n in names.split(",")]

        for name in names:
            if width:
                msb, lsb = map(int, re.findall(r"\d+", width))
                size = abs(msb - lsb) + 1
                signals[name] = [0] * size
            else:
                signals[name] = 0

    # Parse assign statements
    assign_matches = re.findall(r"assign\s+(.+?)\s*=\s*(.+?);", code)
    for lhs, rhs in assign_matches:
        assigns.append((lhs.strip(), rhs.strip()))

    # Parse always blocks
    always_matches = re.findall(
        r"always\s*@\((.*?)\)\s*begin(.*?)end",
        code,
        re.DOTALL
    )

    for sens, body in always_matches:
        always_blocks.append((sens.strip(), body.strip()))

    return signals, assigns, always_blocks


# =========================================================
# 🔧 EXPRESSION ENGINE
# =========================================================

def convert_expr(expr):
    expr = expr.replace("&&", " and ")
    expr = expr.replace("||", " or ")
    expr = expr.replace("&", " & ")
    expr = expr.replace("|", " | ")
    expr = expr.replace("^", " ^ ")
    expr = expr.replace("~", " ~ ")
    return expr


def get_val(signals, name, i=None):
    val = signals[name]
    if isinstance(val, list):
        return val[i]
    return val


def eval_expr(expr, signals, i=None):
    expr_mod = expr

    # Replace indexed signals
    for key in signals:
        if i is not None and f"{key}[{i}]" in expr_mod:
            expr_mod = expr_mod.replace(
                f"{key}[{i}]",
                str(get_val(signals, key, i))
            )

    # Replace scalar signals
    for key in signals:
        expr_mod = re.sub(rf"\b{key}\b", str(signals[key]), expr_mod)

    return eval(expr_mod)


# =========================================================
# 🔧 ASSIGNMENTS
# =========================================================

def assign(signals, target, expr):
    expr = convert_expr(expr)

    # Vector
    if target in signals and isinstance(signals[target], list):
        for i in range(len(signals[target])):
            signals[target][i] = eval_expr(expr, signals, i)
        return

    # Indexed
    if "[" in target:
        name = target.split("[")[0]
        idx = int(re.findall(r"\d+", target)[0])
        signals[name][idx] = eval_expr(expr, signals)
        return

    # Scalar
    signals[target] = eval_expr(expr, signals)


def assign_nb(signals, next_signals, target, expr):
    expr = convert_expr(expr)

    if target in signals and isinstance(signals[target], list):
        next_signals[target] = [
            eval_expr(expr, signals, i)
            for i in range(len(signals[target]))
        ]
        return

    if "[" in target:
        name = target.split("[")[0]
        idx = int(re.findall(r"\d+", target)[0])

        if name not in next_signals:
            next_signals[name] = signals[name].copy()

        next_signals[name][idx] = eval_expr(expr, signals)
        return

    next_signals[target] = eval_expr(expr, signals)


# =========================================================
# 🔧 EXECUTION ENGINE
# =========================================================

def execute_block(lines, signals, next_signals):
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Delay (#5)
        if line.startswith("#"):
            i += 1
            continue

        # IF / ELSE
        if line.startswith("if"):
            cond = re.findall(r"if\s*\((.*?)\)", line)[0]
            cond_val = eval_expr(cond, signals)

            stmt = line.split(")", 1)[1].strip()

            if cond_val:
                if "=" in stmt:
                    lhs, rhs = stmt.split("=")
                    assign_nb(signals, next_signals, lhs.strip(), rhs.strip())
            else:
                if i + 1 < len(lines) and lines[i+1].startswith("else"):
                    else_stmt = lines[i+1].split("else")[1].strip()
                    if "=" in else_stmt:
                        lhs, rhs = else_stmt.split("=")
                        assign_nb(signals, next_signals, lhs.strip(), rhs.strip())
                    i += 1
            i += 1
            continue

        # CASE
        if line.startswith("case"):
            expr = re.findall(r"case\s*\((.*?)\)", line)[0]
            val = eval_expr(expr, signals)

            i += 1
            while i < len(lines) and "endcase" not in lines[i]:
                case_line = lines[i].strip()

                if ":" in case_line:
                    case_val, stmt = case_line.split(":")
                    case_val = case_val.strip()

                    if "b" in case_val:
                        case_val = int(case_val.split("b")[1], 2)
                    else:
                        case_val = int(case_val)

                    if case_val == val:
                        if "=" in stmt:
                            lhs, rhs = stmt.split("=")
                            assign_nb(signals, next_signals, lhs.strip(), rhs.strip())
                        break
                i += 1

            while i < len(lines) and "endcase" not in lines[i]:
                i += 1

            i += 1
            continue

        # BEGIN-END (nested)
        if line.startswith("begin"):
            nested = []
            depth = 1
            i += 1

            while i < len(lines) and depth > 0:
                if "begin" in lines[i]:
                    depth += 1
                if "end" in lines[i]:
                    depth -= 1
                if depth > 0:
                    nested.append(lines[i])
                i += 1

            execute_block(nested, signals, next_signals)
            continue

        # Assignments
        if "<=" in line:
            lhs, rhs = line.split("<=")
            assign_nb(signals, next_signals, lhs.strip(), rhs.strip())

        elif "=" in line:
            lhs, rhs = line.split("=")
            assign(signals, lhs.strip(), rhs.strip())

        i += 1


def execute_always(signals, sens, body, prev_clk):
    lines = [l.strip() for l in body.split(";") if l.strip()]
    next_signals = {}

    clk_match = re.findall(r"(posedge|negedge)\s+(\w+)", sens)

    triggered = False

    if clk_match:
        edge, clk = clk_match[0]
        if edge == "posedge":
            triggered = prev_clk[clk] == 0 and signals[clk] == 1
        else:
            triggered = prev_clk[clk] == 1 and signals[clk] == 0
    else:
        triggered = True

    if not triggered:
        return

    execute_block(lines, signals, next_signals)

    for k, v in next_signals.items():
        signals[k] = v


# =========================================================
# 🧠 AI EXPLANATION ENGINE
# =========================================================

def explain_changes(old, new):
    explanations = []

    for key in new:

        if isinstance(new[key], list):
            for i in range(len(new[key])):
                if old[key][i] != new[key][i]:
                    explanations.append(
                        f"{key}[{i}] changed {old[key][i]} → {new[key][i]}"
                    )
        else:
            if key in old and old[key] != new[key]:
                explanations.append(
                    f"{key} changed {old[key]} → {new[key]}"
                )

    return explanations


# =========================================================
# 🔧 MAIN SIMULATOR
# =========================================================

def simulate(code, input_sequence, cycles=5):

    signals, assigns, always_blocks = parse_verilog(code)
    prev_clk = {k: 0 for k in signals}

    for cycle in range(cycles):
        print(f"\n===== Cycle {cycle} =====")

        old_signals = {
            k: (v.copy() if isinstance(v, list) else v)
            for k, v in signals.items()
        }

        # Apply inputs
        for key, val in input_sequence.items():
            signals[key] = val

        # Combinational
        for lhs, rhs in assigns:
            assign(signals, lhs, rhs)

        # Sequential
        for sens, body in always_blocks:
            execute_always(signals, sens, body, prev_clk)

        # AI Explanation
        changes = explain_changes(old_signals, signals)

        if changes:
            print("\n🧠 AI Explanation:")
            for c in changes:
                print(" -", c)

        # Update clock history
        for k in signals:
            if isinstance(signals[k], int):
                prev_clk[k] = signals[k]

        print("\nSignals:", signals)

    return signals
