# ============================================================
# FILE: backend/placement/grid_mapper.py
# ============================================================

from placement.utils import extract_cell_type


GRID_WIDTH = 12
GRID_HEIGHT = 8


def generate_grid_placement(nodes):

    placement = {}

    row_mapping = {
        "INPUT": 1,
        "ADD": 3,
        "MUX": 3,
        "MUL": 5,
        "FF": 6,
        "OUTPUT": 7
    }

    x_spacing = 2

    row_count = {}

    for node in nodes:

        node_id = node["id"]

        cell_type = extract_cell_type(node_id)

        row = row_mapping.get(cell_type, 4)

        if row not in row_count:
            row_count[row] = 1

        x_position = row_count[row] * x_spacing

        placement[node_id] = (
            x_position,
            row
        )

        row_count[row] += 1

    return placement