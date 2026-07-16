# ================================================================
# DATAPATH LAYER BUILDER
# ================================================================

CONTROL_KEYWORDS = [

    "fsm",
    "state",
    "control",
    "enable",
    "mux"
]

COMPUTE_KEYWORDS = [

    "add",
    "sub",
    "alu",
    "mul",
    "mac",
    "arith"
]

MEMORY_KEYWORDS = [

    "ram",
    "rom",
    "fifo",
    "memory",
    "cache"
]

REGISTER_KEYWORDS = [

    "dff",
    "ff",
    "register",
    "reg"
]


# ================================================================
# LAYER CLASSIFIER
# ================================================================

def classify_cell(cell):

    ctype = str(
        cell.get("type", "")
    ).lower()

    cname = str(
        cell.get("name", "")
    ).lower()

    # ============================================================
    # CONTROL
    # ============================================================

    for keyword in CONTROL_KEYWORDS:

        if keyword in ctype or keyword in cname:

            return "CONTROL_LAYER"

    # ============================================================
    # COMPUTE
    # ============================================================

    for keyword in COMPUTE_KEYWORDS:

        if keyword in ctype or keyword in cname:

            return "COMPUTE_LAYER"

    # ============================================================
    # MEMORY
    # ============================================================

    for keyword in MEMORY_KEYWORDS:

        if keyword in ctype or keyword in cname:

            return "MEMORY_LAYER"

    # ============================================================
    # REGISTER
    # ============================================================

    for keyword in REGISTER_KEYWORDS:

        if keyword in ctype or keyword in cname:

            return "REGISTER_LAYER"

    return "LOGIC_LAYER"


# ================================================================
# BUILD DATAPATH LAYERS
# ================================================================

def build_datapath_layers(

    cells,

    abstractions
):

    layers = {

        "INPUT_LAYER": [],
        "CONTROL_LAYER": [],
        "REGISTER_LAYER": [],
        "COMPUTE_LAYER": [],
        "MEMORY_LAYER": [],
        "LOGIC_LAYER": [],
        "OUTPUT_LAYER": []
    }

    # ============================================================
    # CLASSIFY CELLS
    # ============================================================

    for cell in cells:

        layer = classify_cell(cell)

        layers[layer].append(cell)

    return layers