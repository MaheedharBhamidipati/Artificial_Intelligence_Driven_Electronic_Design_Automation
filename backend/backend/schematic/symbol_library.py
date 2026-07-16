def gate_dimensions(gate_type):
    dims = {
        "AND": (80, 40),
        "OR": (80, 40),
        "XOR": (80, 80),
        "NOT": (60, 40),
        "ADD": (100, 50),
        "SUB": (100, 50),
        "BUFFER": (60, 40),
        "COMPARATOR": (100, 50),
        "DFF": (100, 80)
    }

    return dims.get(gate_type, (90, 60))
