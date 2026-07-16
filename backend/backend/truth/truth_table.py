import re
import itertools
import pandas as pd
import os

# =========================================================
# 🔍 EXTRACT PORTS
# =========================================================
def extract_ports(code):
    pattern = re.findall(r'\b(input|output)\b\s*(?:\[\d+:\d+\])?\s*(\w+)', code)

    inputs = []
    outputs = []

    for typ, name in pattern:
        name = name.strip()

        if typ == "input":
            inputs.append(name)
        elif typ == "output":
            outputs.append(name)

    return inputs, outputs


# =========================================================
# 🔍 EXTRACT ASSIGN STATEMENTS
# =========================================================
def extract_assigns(code):
    assigns = re.findall(r'assign\s+(\w+)\s*=\s*(.*?);', code, re.DOTALL)
    return assigns


# =========================================================
# 🔄 CONVERT VERILOG TO PYTHON
# =========================================================
def convert_expr(expr):
    expr = expr.replace('~', ' not ')
    expr = expr.replace('&', ' and ')
    expr = expr.replace('|', ' or ')
    expr = expr.replace('^', ' ^ ')
    return expr


# =========================================================
# 🧠 SAFE EVALUATION
# =========================================================
def evaluate(expr, values):
    try:
        expr = convert_expr(expr)

        for var, val in values.items():
            expr = re.sub(rf'\b{var}\b', str(val), expr)

        result = eval(expr, {"__builtins__": {}})
        return int(bool(result))

    except:
        return 0   # fallback (no ERR)


# =========================================================
# 🚀 MAIN FUNCTION
# =========================================================
def generate_truth_table(code, report_dir="D:/AI_EDA_TOOL/runs/reports"):

    # ❌ Detect sequential logic → skip
    if "always" in code or "posedge" in code:
        print("⚠️ Sequential circuit detected → truth table not applicable")
        return None

    inputs, outputs = extract_ports(code)
    assigns = extract_assigns(code)

    if not inputs or not assigns:
        print("⚠️ No valid combinational logic found")
        return None

    print("INPUTS:", inputs)
    print("OUTPUTS:", outputs)

    # Limit size
    if len(inputs) > 8:
        print("⚠️ Too many inputs → limiting combinations")
        inputs = inputs[:8]

    combinations = list(itertools.product([0, 1], repeat=len(inputs)))

    rows = []

    for combo in combinations:
        row = dict(zip(inputs, combo))

        for lhs, expr in assigns:
            row[lhs] = evaluate(expr, row)

        rows.append(row)

    df = pd.DataFrame(rows)

    os.makedirs(report_dir, exist_ok=True)
    path = os.path.join(report_dir, "truth_table.csv")
    df.to_csv(path, index=False)

    print(f"Truth table saved → {path}")

    return df
