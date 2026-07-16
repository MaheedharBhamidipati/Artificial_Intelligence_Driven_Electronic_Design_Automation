# ============================================================
# ============================================================
# FILE: backend/placement/utils.py
# ============================================================

def extract_cell_type(node_id):
    

    node_id = node_id.upper()

    if "DFF" in node_id:
        return "FF"

    elif "FF" in node_id:
        return "FF"

    elif "ADD" in node_id:
        return "ADD"

    elif "MUL" in node_id:
        return "MUL"

    elif "MUX" in node_id:
        return "MUX"

    elif "INPUT" in node_id:
        return "INPUT"

    elif "OUTPUT" in node_id:
        return "OUTPUT"

    return "LOGIC"


def normalize_positions(placement_data):

    normalized = {}

    for node, (x, y) in placement_data.items():

        normalized[node] = (
            round(x, 2),
            round(y, 2)
        )

    return normalized