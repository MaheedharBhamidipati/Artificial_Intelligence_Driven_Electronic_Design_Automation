# ============================================================
# MANHATTAN ROUTER
# ============================================================

def generate_manhattan_route(

    source_block,

    target_block
):

    x1 = source_block["center_x"]
    y1 = source_block["center_y"]

    x2 = target_block["center_x"]
    y2 = target_block["center_y"]

    # ========================================================
    # ORTHOGONAL ROUTING
    # ========================================================

    route_points = [

        (x1, y1),

        (x2, y1),

        (x2, y2)
    ]

    return route_points