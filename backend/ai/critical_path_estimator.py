# ================================================================
# CRITICAL PATH ESTIMATOR
# ================================================================

ARITHMETIC_DELAY = 3
MUX_DELAY = 2
REGISTER_DELAY = 1
LOGIC_DELAY = 1


# ================================================================
# CELL DELAY MODEL
# ================================================================

def get_cell_delay(cell):

    ctype = str(
        cell.get("type", "")
    ).lower()

    if any(

        x in ctype

        for x in [

            "add",
            "sub",
            "mul",
            "alu"
        ]
    ):

        return ARITHMETIC_DELAY

    if "mux" in ctype:

        return MUX_DELAY

    if any(

        x in ctype

        for x in [

            "dff",
            "ff",
            "register"
        ]
    ):

        return REGISTER_DELAY

    return LOGIC_DELAY


# ================================================================
# ESTIMATE CRITICAL PATHS
# ================================================================

def estimate_critical_paths(

    cells,

    net_map
):

    paths = []

    for cell in cells:

        delay = get_cell_delay(cell)

        paths.append({

            "cell": cell.get("name"),

            "type": cell.get("type"),

            "estimated_delay": delay
        })

    # ============================================================
    # SORT BY DELAY
    # ============================================================

    paths = sorted(

        paths,

        key=lambda x: x["estimated_delay"],

        reverse=True
    )

    return paths[:20]