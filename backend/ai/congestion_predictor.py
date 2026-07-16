# ================================================================
# CONGESTION PREDICTOR
# ================================================================

def predict_congestion(cells):

    total_connections = 0

    total_cells = len(cells)

    for cell in cells:

        connections = cell.get(

            "connections",

            {}
        )

        total_connections += len(connections)

    if total_cells == 0:

        density = 0

    else:

        density = total_connections / total_cells

    # ============================================================
    # CONGESTION CLASSIFICATION
    # ============================================================

    if density > 12:

        level = "HIGH"

    elif density > 6:

        level = "MEDIUM"

    else:

        level = "LOW"

    return {

        "connection_density": density,

        "congestion_level": level,

        "total_connections": total_connections,

        "total_cells": total_cells
    }